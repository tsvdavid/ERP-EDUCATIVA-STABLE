# apps/data_engine/progress/tracker.py
"""Concrete ProgressTracker implementation (`BaseProgressTracker`).

Tracks real-time progress across phase, batch, and node levels for an active import session.
Calculates Throughput (`records_processed / elapsed_seconds`) and Estimated Time of Arrival (ETA)
using monotonic timestamps to prevent system clock drift.
Emits immutable `ProgressEvent` milestones to all subscribed `BaseProgressObserver` instances.
"""

import time
import uuid
from typing import Any, Dict, List, Optional, Set

from .base import BaseProgressObserver, BaseProgressTracker
from .models import ProgressEvent, ProgressEventType, ProgressSnapshot


class ProgressTracker(BaseProgressTracker):
    """Subject responsible for tracking live progress and notifying observers.

    Parameters
    ----------
    session_id: str
        Unique UUID or string identifying the session being tracked.
    run_id: Optional[str]
        Identifier for the specific execution run (defaults to a generated UUID).
    total_expected_records: int
        Expected total records to be processed across the session (can be 0 or updated dynamically).
    """

    def __init__(
        self,
        session_id: str,
        run_id: Optional[str] = None,
        total_expected_records: int = 0,
    ):
        if not session_id:
            raise ValueError("session_id is required and cannot be empty")
        if total_expected_records < 0:
            raise ValueError("total_expected_records must be non-negative")

        self._session_id = session_id
        self._run_id = run_id or str(uuid.uuid4())
        self._state = "CREATED"
        self._current_phase = ""
        self._overall_percentage = 0.0

        self._total_records_expected = total_expected_records
        self._records_processed = 0
        self._records_accepted = 0
        self._records_rejected = 0
        self._records_skipped = 0

        self._start_time_monotonic: Optional[float] = None
        self._phase_start_monotonic: Dict[str, float] = {}
        self._phase_durations_ms: Dict[str, float] = {}

        self._current_batch_index: Optional[int] = None
        self._total_batches: Optional[int] = None
        self._current_node_id: Optional[str] = None

        self._metadata: Dict[str, Any] = {}
        self._observers: Set[BaseProgressObserver] = set()

    def subscribe(self, observer: BaseProgressObserver) -> None:
        """Register an observer to receive future progress events."""
        if not isinstance(observer, BaseProgressObserver):
            raise TypeError("observer must implement BaseProgressObserver")
        self._observers.add(observer)

    def unsubscribe(self, observer: BaseProgressObserver) -> None:
        """Unregister an observer from receiving progress events."""
        if observer in self._observers:
            self._observers.remove(observer)

    def emit(
        self,
        event_type: ProgressEventType,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProgressEvent:
        """Generate a new ProgressEvent from the live snapshot and notify all subscribed observers."""
        snapshot = self.get_snapshot()
        event = ProgressEvent.create(
            session_id=self._session_id,
            event_type=event_type,
            snapshot=snapshot,
            message=message,
            metadata=metadata,
        )
        for observer in list(self._observers):
            try:
                observer.on_progress(event)
            except Exception:
                # Observers must not crash the tracking loop
                pass
        return event

    def get_snapshot(self) -> ProgressSnapshot:
        """Construct and return an immutable live ProgressSnapshot DTO."""
        elapsed_ms, throughput, eta_seconds, percentage = self._compute_performance_metrics()
        return ProgressSnapshot(
            session_id=self._session_id,
            run_id=self._run_id,
            state=self._state,
            current_phase=self._current_phase,
            overall_percentage=percentage,
            total_records_expected=self._total_records_expected,
            records_processed=self._records_processed,
            records_accepted=self._records_accepted,
            records_rejected=self._records_rejected,
            records_skipped=self._records_skipped,
            elapsed_duration_ms=elapsed_ms,
            phase_durations_ms=dict(self._phase_durations_ms),
            throughput_records_sec=throughput,
            estimated_eta_seconds=eta_seconds,
            current_batch_index=self._current_batch_index,
            total_batches=self._total_batches,
            current_node_id=self._current_node_id,
            metadata=dict(self._metadata),
        )

    def record_session_start(self, total_expected_records: int = 0) -> None:
        """Record the initiation of an import session and start overall timing counters."""
        if total_expected_records > 0:
            self._total_records_expected = total_expected_records
        self._state = "RUNNING"
        self._start_time_monotonic = time.monotonic()
        self.emit(
            ProgressEventType.SESSION_START,
            f"Session '{self._session_id}' started with {self._total_records_expected} expected records.",
        )

    def record_phase_start(self, phase_name: str, total_records: Optional[int] = None) -> None:
        """Record the start of a specific pipeline phase."""
        if not phase_name:
            raise ValueError("phase_name must be non-empty")
        if self._start_time_monotonic is None:
            self.record_session_start()
        if total_records is not None and total_records > 0:
            self._total_records_expected = total_records

        self._current_phase = phase_name
        self._phase_start_monotonic[phase_name] = time.monotonic()
        self.emit(
            ProgressEventType.PHASE_START,
            f"Phase '{phase_name}' started.",
            {"phase": phase_name},
        )

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
        if not phase_name:
            raise ValueError("phase_name must be non-empty")
        if processed < 0 or accepted < 0 or rejected < 0 or skipped < 0:
            raise ValueError("Record counts cannot be negative")

        self._current_phase = phase_name
        self._records_processed = processed
        self._records_accepted = accepted
        self._records_rejected = rejected
        self._records_skipped = skipped

        self.emit(
            ProgressEventType.PHASE_PROGRESS,
            message,
            {"phase": phase_name},
        )

    def record_phase_end(
        self,
        phase_name: str,
        success: bool,
        output_records: int,
        errors: Optional[List[str]] = None,
    ) -> None:
        """Record the completion or failure of a pipeline phase."""
        if not phase_name:
            raise ValueError("phase_name must be non-empty")

        start_t = self._phase_start_monotonic.get(phase_name, time.monotonic())
        duration_ms = max(0.0, (time.monotonic() - start_t) * 1000.0)
        self._phase_durations_ms[phase_name] = duration_ms

        if output_records >= 0:
            self._records_processed = max(self._records_processed, output_records)

        err_list = list(errors) if errors else []
        self._metadata[f"{phase_name}_success"] = success
        if err_list:
            self._metadata[f"{phase_name}_errors"] = err_list

        self.emit(
            ProgressEventType.PHASE_END,
            f"Phase '{phase_name}' completed (success={success}, duration={duration_ms:.2f}ms).",
            {"phase": phase_name, "success": success, "duration_ms": duration_ms, "errors": err_list},
        )

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
        if batch_index < 0 or total_batches < 0:
            raise ValueError("batch indices must be non-negative")

        self._current_batch_index = batch_index
        self._total_batches = total_batches
        self._records_processed += records_in_batch
        self._records_accepted += accepted_in_batch
        self._records_rejected += rejected_in_batch
        self._records_skipped += skipped_in_batch

        event_type = ProgressEventType.BATCH_PROGRESS
        if batch_index == 1:
            event_type = ProgressEventType.BATCH_START
        elif batch_index == total_batches and total_batches > 0:
            event_type = ProgressEventType.BATCH_END

        self.emit(
            event_type,
            f"Batch {batch_index}/{total_batches} processed ({records_in_batch} records).",
            {"batch_index": batch_index, "total_batches": total_batches, "records_in_batch": records_in_batch},
        )

    def record_node_progress(
        self,
        node_id: str,
        state: str,
        records_affected: int = 0,
        error: Optional[str] = None,
    ) -> None:
        """Record the execution progress or state transition of a specific DAG `LoadNode`."""
        if not node_id:
            raise ValueError("node_id must be non-empty")

        self._current_node_id = node_id
        if records_affected > 0:
            self._records_processed += records_affected
            if state.upper() == "COMPLETED":
                self._records_accepted += records_affected
            elif state.upper() == "FAILED":
                self._records_rejected += records_affected

        event_type = ProgressEventType.NODE_PROGRESS
        if state.upper() == "RUNNING":
            event_type = ProgressEventType.NODE_START
        elif state.upper() in ("COMPLETED", "FAILED", "SKIPPED"):
            event_type = ProgressEventType.NODE_END

        meta = {"node_id": node_id, "state": state}
        if error:
            meta["error"] = error

        self.emit(
            event_type,
            f"Node '{node_id}' state changed to {state}.",
            meta,
        )

    def record_session_end(self, final_state: str = "COMPLETED", message: Optional[str] = None) -> None:
        """Record the successful conclusion of the overall import session."""
        self._state = final_state
        if final_state.upper() == "COMPLETED":
            self._overall_percentage = 100.0
        msg = message or f"Session '{self._session_id}' finished with state '{final_state}'."
        self.emit(ProgressEventType.SESSION_END, msg, {"final_state": final_state})

    def record_session_abort(self, reason: str, final_state: str = "FAILED") -> None:
        """Record the abortion or terminal failure of the import session."""
        self._state = final_state
        self.emit(
            ProgressEventType.SESSION_ABORT,
            f"Session '{self._session_id}' aborted: {reason}",
            {"reason": reason, "final_state": final_state},
        )

    def _compute_performance_metrics(self) -> tuple[float, float, float, float]:
        """Compute live elapsed duration, throughput (records/sec), estimated ETA, and percentage."""
        if self._start_time_monotonic is None:
            return 0.0, 0.0, 0.0, self._overall_percentage

        elapsed_sec = max(0.001, time.monotonic() - self._start_time_monotonic)
        elapsed_ms = elapsed_sec * 1000.0

        throughput = self._records_processed / elapsed_sec if elapsed_sec > 0 else 0.0

        if self._total_records_expected > 0 and self._records_processed < self._total_records_expected and throughput > 0:
            eta_seconds = (self._total_records_expected - self._records_processed) / throughput
        else:
            eta_seconds = 0.0

        if self._state in ("COMPLETED", "FAILED", "ABORTED"):
            if self._state == "COMPLETED":
                percentage = 100.0
            elif self._total_records_expected > 0:
                percentage = min(100.0, max(0.0, (self._records_processed / self._total_records_expected) * 100.0))
            else:
                percentage = self._overall_percentage
        else:
            if self._total_records_expected > 0:
                percentage = min(100.0, max(0.0, (self._records_processed / self._total_records_expected) * 100.0))
            else:
                # Fallback step-based percentage estimate if total records is 0
                phase_weights = {
                    "Reader": 10.0,
                    "Parser": 20.0,
                    "Validation": 30.0,
                    "Mapping": 40.0,
                    "Schema & Caster": 50.0,
                    "Staging": 60.0,
                    "Reconciliation": 70.0,
                    "Loader Planning": 80.0,
                    "Execution Engine": 90.0,
                    "Persistence Adapter": 95.0,
                }
                percentage = phase_weights.get(self._current_phase, self._overall_percentage)

        return elapsed_ms, throughput, eta_seconds, percentage
