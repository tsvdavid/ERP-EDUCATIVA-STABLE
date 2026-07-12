# apps/data_engine/jobs/manager.py
"""JobManager — Central Orchestrator for Distributed Background Jobs (TAREA 24).

Administers the lifecycle of long-running data import sessions outside the HTTP
request/response cycle. Coordinates with `BaseJobStore` for state persistence,
`BaseJobQueue` for asynchronous dispatch, `MacApplicationFacade` for domain execution,
and `EventBusRegistry` for real-time notification broadcasting.
"""

import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from apps.data_engine.application.dto import ImportRequest
from apps.data_engine.application.exceptions import ValidationException
from apps.data_engine.application.facade import MacApplicationFacade
from apps.data_engine.events.models import EventCategory, EventEnvelope
from apps.data_engine.events.registry import EventBusRegistry
from .contracts import BaseJobRunner, JobConfig, JobRecord, JobStatus
from .exceptions import (
    JobCancelledException,
    JobException,
    JobNotFoundException,
    JobRetryExceededException,
)
from .registry import JobRegistry


class JobManager(BaseJobRunner):
    """Singleton Manager for asynchronous background job scheduling and execution."""

    _instance: Optional["JobManager"] = None
    _singleton_lock = threading.Lock()

    def __init__(self, registry: Optional[JobRegistry] = None):
        self.registry = registry or JobRegistry.global_registry()
        self.facade = MacApplicationFacade()

    @classmethod
    def global_instance(cls) -> "JobManager":
        """Return the global singleton JobManager instance."""
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_global_instance(cls) -> None:
        """Reset the global singleton (primarily for isolated test cleanup)."""
        with cls._singleton_lock:
            cls._instance = None

    def _emit_event(
        self,
        event_type: str,
        session_id: str,
        payload: Dict[str, Any],
        tenant_id: Optional[str] = None,
        category: EventCategory = EventCategory.SYSTEM,
    ) -> None:
        """Helper to publish real-time notifications to the global EventBus."""
        try:
            dispatcher = EventBusRegistry.global_registry().get_dispatcher()
            envelope = EventEnvelope.create(
                category=category,
                event_type=event_type,
                session_id=session_id,
                payload=payload,
                source="jobs",
                tenant_id=tenant_id,
            )
            dispatcher.publish(envelope)
        except Exception:
            # Event emission failures must never crash job state transitions
            pass

    def create_and_enqueue(
        self,
        tenant_id: str,
        user_id: str,
        source: Any = None,
        pipeline_config: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        config: Optional[JobConfig] = None,
        run_id: Optional[str] = None,
        is_resume: bool = False,
    ) -> JobRecord:
        """Create a new JobRecord and submit it to the queue adapter."""
        job_id = str(uuid.uuid4())
        sess_id = session_id or str(uuid.uuid4())
        job_config = config or JobConfig()

        record = JobRecord(
            job_id=job_id,
            session_id=sess_id,
            tenant_id=tenant_id,
            user_id=user_id,
            status=JobStatus.QUEUED,
            config=job_config,
            created_at=time.time(),
        )

        store = self.registry.get_store()
        store.save(record)

        # Enqueue with kwargs required for execution
        queue = self.registry.get_queue()
        queue.enqueue(
            job_id=job_id,
            config=job_config,
            source=source,
            pipeline_config=pipeline_config or {},
            run_id=run_id,
            is_resume=is_resume,
        )

        self._emit_event(
            event_type="JOB_QUEUED",
            session_id=sess_id,
            payload={
                "job_id": job_id,
                "tenant_id": tenant_id,
                "status": JobStatus.QUEUED.value,
                "queue_name": job_config.queue_name,
            },
            tenant_id=tenant_id,
        )

        return record

    def get_job(self, job_id: str) -> JobRecord:
        """Retrieve a JobRecord by its unique ID."""
        store = self.registry.get_store()
        record = store.get(job_id)
        if record is None:
            raise JobNotFoundException(f"Job with ID {job_id} not found.")
        return record

    def list_jobs(self, tenant_id: str, limit: int = 50) -> List[JobRecord]:
        """List job records for a given tenant."""
        store = self.registry.get_store()
        return store.list_by_tenant(tenant_id, limit=limit)

    def cancel_job(self, job_id: str) -> JobRecord:
        """Cancel a queued or running job."""
        store = self.registry.get_store()
        record = self.get_job(job_id)

        if record.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            return record

        queue = self.registry.get_queue()
        queue.cancel(job_id)

        # If job is already running, attempt to cancel the underlying session via facade
        if record.status == JobStatus.RUNNING:
            try:
                self.facade.cancel(record.session_id)
            except Exception:
                pass

        updated = record.with_status(
            status=JobStatus.CANCELLED,
            finished_at=time.time(),
        )
        store.save(updated)

        self._emit_event(
            event_type="JOB_CANCELLED",
            session_id=updated.session_id,
            payload={
                "job_id": job_id,
                "status": JobStatus.CANCELLED.value,
            },
            tenant_id=updated.tenant_id,
        )

        return updated

    def retry_job(self, job_id: str) -> JobRecord:
        """Force manual retry of a failed or paused job."""
        store = self.registry.get_store()
        record = self.get_job(job_id)

        if record.status not in (JobStatus.FAILED, JobStatus.RETRYING):
            raise JobException(f"Cannot retry job in state {record.status.value}")

        updated = record.with_status(
            status=JobStatus.QUEUED,
            error_message=None,
            retry_count=record.retry_count + 1,
        )
        store.save(updated)

        queue = self.registry.get_queue()
        queue.enqueue(job_id=job_id, config=updated.config, is_resume=True)

        self._emit_event(
            event_type="JOB_QUEUED",
            session_id=updated.session_id,
            payload={
                "job_id": job_id,
                "status": JobStatus.QUEUED.value,
                "retry_count": updated.retry_count,
            },
            tenant_id=updated.tenant_id,
        )
        return updated

    def run_job(self, job_id: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute the job workflow within the worker process/thread.

        Implements `BaseJobRunner.run_job`.
        """
        store = self.registry.get_store()
        record = store.get(job_id)
        if record is None:
            raise JobNotFoundException(f"Job with ID {job_id} not found.")

        if record.status == JobStatus.CANCELLED:
            raise JobCancelledException(f"Job {job_id} has been cancelled.")

        # Transition to RUNNING
        running_record = record.with_status(
            status=JobStatus.RUNNING,
            started_at=time.time() if record.started_at is None else record.started_at,
        )
        store.save(running_record)

        self._emit_event(
            event_type="JOB_STARTED",
            session_id=running_record.session_id,
            payload={
                "job_id": job_id,
                "status": JobStatus.RUNNING.value,
                "retry_count": running_record.retry_count,
            },
            tenant_id=running_record.tenant_id,
        )

        source = kwargs.get("source")
        pipeline_config = kwargs.get("pipeline_config", {})
        run_id = kwargs.get("run_id")
        is_resume = kwargs.get("is_resume", False)

        try:
            res_dto = None
            if is_resume:
                try:
                    res_dto = self.facade.resume(running_record.session_id)
                except Exception:
                    # Fallback to fresh start if session was never checkpointed due to early crash
                    res_dto = None

            if res_dto is None:
                req_dto = ImportRequest(
                    tenant_id=running_record.tenant_id,
                    user_id=running_record.user_id,
                    source=source or "stream.csv",
                    pipeline_config=pipeline_config,
                    run_id=run_id,
                    is_dry_run=False,
                )
                res_dto = self.facade.start_import(req_dto)

            result_data = {
                "session_id": res_dto.session_id,
                "run_id": res_dto.run_id,
                "state": res_dto.state,
                "total_records": res_dto.total_records,
                "processed_records": res_dto.processed_records,
                "errors": res_dto.errors,
                "is_success": res_dto.is_success,
            }

            if not res_dto.is_success and res_dto.errors:
                # Treat unhandled critical errors returned in payload if any
                err_msg = str(res_dto.errors[0]) if res_dto.errors else "Execution finished with failures."
                if running_record.retry_count < running_record.config.max_retries:
                    return self._handle_retry(running_record, err_msg, kwargs)
                else:
                    return self._handle_failure(running_record, err_msg)

            completed_record = running_record.with_status(
                status=JobStatus.COMPLETED,
                finished_at=time.time(),
                result=result_data,
            )
            store.save(completed_record)

            self._emit_event(
                event_type="JOB_COMPLETED",
                session_id=completed_record.session_id,
                payload={
                    "job_id": job_id,
                    "status": JobStatus.COMPLETED.value,
                    "result": result_data,
                },
                tenant_id=completed_record.tenant_id,
            )
            return result_data

        except Exception as exc:
            # Check if non-retryable fatal exception
            if isinstance(exc, (ValidationException, JobCancelledException)):
                return self._handle_failure(running_record, str(exc))

            if running_record.retry_count < running_record.config.max_retries:
                return self._handle_retry(running_record, str(exc), kwargs)
            else:
                return self._handle_failure(running_record, str(exc))

    def _handle_retry(self, record: JobRecord, error_msg: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule automatic retry with backoff."""
        store = self.registry.get_store()
        queue = self.registry.get_queue()

        updated = record.with_status(
            status=JobStatus.RETRYING,
            error_message=error_msg,
            retry_count=record.retry_count + 1,
        )
        store.save(updated)

        # Enqueue retry
        delay = updated.config.retry_delay_seconds
        kwargs["is_resume"] = True
        queue.enqueue(
            job_id=updated.job_id,
            config=updated.config,
            delay_seconds=delay,
            **kwargs,
        )

        self._emit_event(
            event_type="JOB_RETRYING",
            session_id=updated.session_id,
            payload={
                "job_id": updated.job_id,
                "status": JobStatus.RETRYING.value,
                "retry_count": updated.retry_count,
                "max_retries": updated.config.max_retries,
                "error_message": error_msg,
                "retry_delay_seconds": delay,
            },
            tenant_id=updated.tenant_id,
        )

        return {"job_id": updated.job_id, "status": JobStatus.RETRYING.value, "retry_count": updated.retry_count}

    def _handle_failure(self, record: JobRecord, error_msg: str) -> Dict[str, Any]:
        """Mark job as permanently failed after exhausting retries or fatal error."""
        store = self.registry.get_store()
        updated = record.with_status(
            status=JobStatus.FAILED,
            error_message=error_msg,
            finished_at=time.time(),
        )
        store.save(updated)

        self._emit_event(
            event_type="JOB_FAILED",
            session_id=updated.session_id,
            payload={
                "job_id": updated.job_id,
                "status": JobStatus.FAILED.value,
                "error_message": error_msg,
                "retry_count": updated.retry_count,
            },
            tenant_id=updated.tenant_id,
        )

        return {"job_id": updated.job_id, "status": JobStatus.FAILED.value, "error": error_msg}
