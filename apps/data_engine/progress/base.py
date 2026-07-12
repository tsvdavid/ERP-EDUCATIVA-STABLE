# apps/data_engine/progress/base.py
"""Abstract contracts for the Progress Tracking & Real-Time Monitoring Framework.

Defines the core Subject/Observer interfaces (`BaseProgressTracker`, `BaseProgressObserver`,
and `BaseProgressStore`) enforcing Dependency Inversion and complete decoupling from transport
or ORM persistence layers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .models import ProgressEvent, ProgressSnapshot, ProgressEventType


class BaseProgressObserver(ABC):
    """Abstract interface for consumers observing real-time progress events.

    Implementations can include WebSocket broadcasters, REST webhook triggers,
    in-memory history collectors, or logging sinks.
    """

    @abstractmethod
    def on_progress(self, event: ProgressEvent) -> None:
        """Receive and process a real-time progress event emitted by a tracker."""
        raise NotImplementedError


class BaseProgressTracker(ABC):
    """Abstract Subject contract responsible for tracking pipeline progress and notifying observers."""

    @abstractmethod
    def subscribe(self, observer: BaseProgressObserver) -> None:
        """Register an observer to receive future progress events."""
        raise NotImplementedError

    @abstractmethod
    def unsubscribe(self, observer: BaseProgressObserver) -> None:
        """Unregister an observer from receiving progress events."""
        raise NotImplementedError

    @abstractmethod
    def emit(
        self,
        event_type: ProgressEventType,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProgressEvent:
        """Generate a new ProgressEvent from the current state and notify all subscribed observers."""
        raise NotImplementedError

    @abstractmethod
    def get_snapshot(self) -> ProgressSnapshot:
        """Construct and return an immutable live ProgressSnapshot DTO."""
        raise NotImplementedError

    @abstractmethod
    def record_session_start(self, total_expected_records: int = 0) -> None:
        """Record the initiation of an import session and start overall timing counters."""
        raise NotImplementedError

    @abstractmethod
    def record_phase_start(self, phase_name: str, total_records: Optional[int] = None) -> None:
        """Record the start of a specific pipeline phase."""
        raise NotImplementedError

    @abstractmethod
    def record_phase_progress(
        self,
        phase_name: str,
        processed: int,
        accepted: int = 0,
        rejected: int = 0,
        skipped: int = 0,
        message: str = "Phase progress updated",
    ) -> None:
        """Record incremental record processing progress within the current phase."""
        raise NotImplementedError

    @abstractmethod
    def record_phase_end(
        self,
        phase_name: str,
        success: bool,
        output_records: int,
        errors: Optional[List[str]] = None,
    ) -> None:
        """Record the completion or failure of a pipeline phase."""
        raise NotImplementedError

    @abstractmethod
    def record_batch_progress(
        self,
        batch_index: int,
        total_batches: int,
        records_in_batch: int,
        accepted_in_batch: int = 0,
        rejected_in_batch: int = 0,
        skipped_in_batch: int = 0,
    ) -> None:
        """Record granular batch/chunk processing milestones during ingestion or transformation."""
        raise NotImplementedError

    @abstractmethod
    def record_node_progress(
        self,
        node_id: str,
        state: str,
        records_affected: int = 0,
        error: Optional[str] = None,
    ) -> None:
        """Record the execution progress or state transition of a specific DAG `LoadNode`."""
        raise NotImplementedError

    @abstractmethod
    def record_session_end(self, final_state: str = "COMPLETED", message: Optional[str] = None) -> None:
        """Record the successful conclusion of the overall import session."""
        raise NotImplementedError

    @abstractmethod
    def record_session_abort(self, reason: str, final_state: str = "FAILED") -> None:
        """Record the abortion or terminal failure of the import session."""
        raise NotImplementedError


class BaseProgressStore(BaseProgressObserver):
    """Abstract contract for optional persistence adapters storing progress history.

    Concrete implementations relying on Django ORM must reside strictly within
    `apps/data_engine/persistence/` to adhere to the Zero-ORM boundary.
    """

    @abstractmethod
    def save_snapshot(self, snapshot: ProgressSnapshot) -> None:
        """Persist the latest snapshot to the storage medium."""
        raise NotImplementedError
