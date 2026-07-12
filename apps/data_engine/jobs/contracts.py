# apps/data_engine/jobs/contracts.py
"""Domain Contracts for Background Processing & Distributed Job Framework (TAREA 24).

Defines core enumerations, configuration dataclasses, state tracking DTOs, and abstract
interfaces for storage (`BaseJobStore`), enqueuing (`BaseJobQueue`), and execution (`BaseJobRunner`).
All classes are Zero-ORM and independent of specific message brokers or frameworks.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time


class JobStatus(str, Enum):
    """Lifecycle states for asynchronous background jobs."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class JobConfig:
    """Immutable configuration rules and execution parameters for a background job."""
    queue_name: str = "mac_jobs"
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 3600
    priority: int = 0


_UNSET = object()


@dataclass(frozen=True)
class JobRecord:
    """Immutable snapshot DTO tracking the full state and history of a background job."""
    job_id: str
    session_id: str
    tenant_id: str
    user_id: str
    status: JobStatus = JobStatus.QUEUED
    config: JobConfig = field(default_factory=JobConfig)
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None

    def with_status(
        self,
        status: JobStatus,
        error_message: Any = _UNSET,
        retry_count: Optional[int] = None,
        started_at: Optional[float] = None,
        finished_at: Optional[float] = None,
        result: Any = _UNSET,
    ) -> "JobRecord":
        """Return a new JobRecord instance reflecting status and tracking updates."""
        return JobRecord(
            job_id=self.job_id,
            session_id=self.session_id,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            status=status,
            config=self.config,
            error_message=self.error_message if error_message is _UNSET else error_message,
            retry_count=retry_count if retry_count is not None else self.retry_count,
            created_at=self.created_at,
            started_at=started_at if started_at is not None else self.started_at,
            finished_at=finished_at if finished_at is not None else self.finished_at,
            result=self.result if result is _UNSET else result,
        )


class BaseJobStore(ABC):
    """Abstract contract for persisting and retrieving `JobRecord` state."""

    @abstractmethod
    def save(self, record: JobRecord) -> None:
        """Persist or update a job record."""
        pass

    @abstractmethod
    def get(self, job_id: str) -> Optional[JobRecord]:
        """Retrieve a job record by its unique ID, or return None if missing."""
        pass

    @abstractmethod
    def list_by_tenant(self, tenant_id: str, limit: int = 50) -> List[JobRecord]:
        """List job records belonging to a specific tenant."""
        pass

    @abstractmethod
    def delete(self, job_id: str) -> bool:
        """Remove a job record from the store."""
        pass


class BaseJobQueue(ABC):
    """Abstract contract for enqueuing and revoking asynchronous job tasks."""

    @abstractmethod
    def enqueue(self, job_id: str, config: JobConfig, delay_seconds: int = 0, **kwargs: Any) -> str:
        """Submit a job ID to the underlying queue broker for execution.

        Returns the broker task ID (or job_id).
        """
        pass

    @abstractmethod
    def cancel(self, job_id: str, task_id: Optional[str] = None) -> bool:
        """Request cancellation/revocation of an enqueued or running job in the broker."""
        pass


class BaseJobRunner(ABC):
    """Abstract contract for executing a job within a worker process/thread."""

    @abstractmethod
    def run_job(self, job_id: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute the job logic and return summary results."""
        pass
