# apps/data_engine/jobs/adapters.py
"""Adapters for Background Processing & Distributed Job Framework (TAREA 24).

Contains thread-safe in-memory implementations (`InMemoryJobStore`, `InMemoryJobQueue`)
for deterministic `Zero-ORM` unit/integration testing, alongside `CeleryJobAdapter`
for distributed production workloads via Celery task queues.
"""

import threading
from typing import Any, Dict, List, Optional

from .contracts import BaseJobQueue, BaseJobStore, JobConfig, JobRecord
from .exceptions import JobException


class InMemoryJobStore(BaseJobStore):
    """Thread-safe in-memory storage adapter for `JobRecord` state persistence."""

    def __init__(self):
        self._records: Dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def save(self, record: JobRecord) -> None:
        """Persist or update a job record in the memory map."""
        if not isinstance(record, JobRecord):
            raise TypeError(f"Expected JobRecord, got {type(record).__name__}")
        with self._lock:
            self._records[record.job_id] = record

    def get(self, job_id: str) -> Optional[JobRecord]:
        """Retrieve a job record by ID."""
        with self._lock:
            return self._records.get(job_id)

    def list_by_tenant(self, tenant_id: str, limit: int = 50) -> List[JobRecord]:
        """List job records belonging to a specific tenant, sorted by creation time descending."""
        with self._lock:
            filtered = [
                rec for rec in self._records.values() if rec.tenant_id == tenant_id
            ]
            filtered.sort(key=lambda r: r.created_at, reverse=True)
            return filtered[:limit]

    def delete(self, job_id: str) -> bool:
        """Remove a job record from the memory store."""
        with self._lock:
            if job_id in self._records:
                del self._records[job_id]
                return True
            return False

    def clear(self) -> None:
        """Clear all records from storage."""
        with self._lock:
            self._records.clear()


class InMemoryJobQueue(BaseJobQueue):
    """Thread-safe in-memory queue adapter for deterministic job submission and testing."""

    def __init__(self, auto_run: bool = False):
        self.auto_run = auto_run
        self.queued_tasks: Dict[str, Dict[str, Any]] = {}
        self.cancelled_job_ids: set = set()
        self._lock = threading.Lock()

    def enqueue(self, job_id: str, config: JobConfig, delay_seconds: int = 0, **kwargs: Any) -> str:
        """Enqueue a job ID and its execution arguments."""
        with self._lock:
            self.queued_tasks[job_id] = {
                "job_id": job_id,
                "config": config,
                "delay_seconds": delay_seconds,
                "kwargs": kwargs,
            }
            self.cancelled_job_ids.discard(job_id)

        if self.auto_run and delay_seconds <= 0:
            self.run_sync(job_id)

        return job_id

    def cancel(self, job_id: str, task_id: Optional[str] = None) -> bool:
        """Mark a job as cancelled and remove from queued items."""
        with self._lock:
            self.cancelled_job_ids.add(job_id)
            if job_id in self.queued_tasks:
                del self.queued_tasks[job_id]
            return True

    def run_sync(self, job_id: str) -> Dict[str, Any]:
        """Synchronously trigger execution of a queued job for testing/debugging."""
        with self._lock:
            if job_id in self.cancelled_job_ids:
                raise JobException(f"Cannot run job {job_id} because it was cancelled in queue.")
            task_info = self.queued_tasks.pop(job_id, None)

        if not task_info:
            raise JobException(f"Job {job_id} is not queued in memory.")

        from .registry import JobRegistry
        runner = JobRegistry.global_registry().get_runner()
        return runner.run_job(job_id, **task_info["kwargs"])

    def clear(self) -> None:
        """Clear all queued and cancelled tasks."""
        with self._lock:
            self.queued_tasks.clear()
            self.cancelled_job_ids.clear()


class CeleryJobAdapter(BaseJobQueue):
    """Distributed queue adapter connecting to Celery workers via `send_task`."""

    def __init__(self, celery_app: Any = None):
        self._celery_app = celery_app

    @property
    def celery_app(self) -> Any:
        """Resolve the active Celery app instance."""
        if self._celery_app is not None:
            return self._celery_app
        try:
            from celery import current_app
            return current_app
        except ImportError:
            raise JobException("Celery library is not installed or available.")

    def enqueue(self, job_id: str, config: JobConfig, delay_seconds: int = 0, **kwargs: Any) -> str:
        """Dispatch job execution to a remote Celery worker."""
        task_name = "apps.data_engine.jobs.tasks.run_mac_job"
        async_result = self.celery_app.send_task(
            task_name,
            args=[job_id],
            kwargs=kwargs,
            queue=config.queue_name,
            countdown=delay_seconds if delay_seconds > 0 else None,
            priority=config.priority,
        )
        return str(getattr(async_result, "id", job_id))

    def cancel(self, job_id: str, task_id: Optional[str] = None) -> bool:
        """Revoke and terminate a task on remote Celery workers."""
        target_id = task_id or job_id
        try:
            self.celery_app.control.revoke(target_id, terminate=True)
            return True
        except Exception:
            return False
