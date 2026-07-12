# apps/data_engine/progress/models.py
"""Domain models and DTOs for the Progress Tracking & Real-Time Monitoring Framework.

Provides immutable Value Objects and DTOs (`ProgressEventType`, `ProgressSnapshot`,
`ProgressEvent`) representing multi-level progress tracking (phase, batch, and node levels)
across the MAC pipeline. Strictly decoupled from Django ORM and transport layers (Zero-ORM policy).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ProgressEventType(str, Enum):
    """Granular event types emitted by the ProgressTracker during lifecycle transitions."""

    SESSION_START = "SESSION_START"
    SESSION_PROGRESS = "SESSION_PROGRESS"
    SESSION_END = "SESSION_END"
    SESSION_ABORT = "SESSION_ABORT"

    PHASE_START = "PHASE_START"
    PHASE_PROGRESS = "PHASE_PROGRESS"
    PHASE_END = "PHASE_END"

    BATCH_START = "BATCH_START"
    BATCH_PROGRESS = "BATCH_PROGRESS"
    BATCH_END = "BATCH_END"

    NODE_START = "NODE_START"
    NODE_PROGRESS = "NODE_PROGRESS"
    NODE_END = "NODE_END"


@dataclass(frozen=True)
class ProgressSnapshot:
    """Immutable DTO representing the instant live state and performance metrics of a session.

    Can be safely serialized (`to_dict()`) and transmitted over REST APIs, WebSockets, or SSE
    without coupling to any transport implementation.
    """

    session_id: str
    run_id: str
    state: str
    current_phase: str
    overall_percentage: float

    # Record metrics
    total_records_expected: int
    records_processed: int
    records_accepted: int
    records_rejected: int
    records_skipped: int

    # Timing and performance metrics
    elapsed_duration_ms: float
    phase_durations_ms: Dict[str, float]
    throughput_records_sec: float
    estimated_eta_seconds: float

    # Granular batch and node context
    current_batch_index: Optional[int] = None
    total_batches: Optional[int] = None
    current_node_id: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the snapshot to a clean JSON-serializable dictionary."""
        return {
            "session_id": self.session_id,
            "run_id": self.run_id,
            "state": self.state,
            "current_phase": self.current_phase,
            "overall_percentage": round(self.overall_percentage, 2),
            "total_records_expected": self.total_records_expected,
            "records_processed": self.records_processed,
            "records_accepted": self.records_accepted,
            "records_rejected": self.records_rejected,
            "records_skipped": self.records_skipped,
            "elapsed_duration_ms": round(self.elapsed_duration_ms, 2),
            "phase_durations_ms": {k: round(v, 2) for k, v in self.phase_durations_ms.items()},
            "throughput_records_sec": round(self.throughput_records_sec, 2),
            "estimated_eta_seconds": round(self.estimated_eta_seconds, 2),
            "current_batch_index": self.current_batch_index,
            "total_batches": self.total_batches,
            "current_node_id": self.current_node_id,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ProgressEvent:
    """Immutable audit event representing a specific progress milestone or state change.

    Contains the exact `ProgressSnapshot` at the moment the event was generated.
    """

    event_id: str
    session_id: str
    event_type: ProgressEventType
    snapshot: ProgressSnapshot
    message: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        session_id: str,
        event_type: ProgressEventType,
        snapshot: ProgressSnapshot,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ProgressEvent":
        """Factory helper to instantiate a new ProgressEvent with a generated UUID and UTC timestamp."""
        return cls(
            event_id=str(uuid.uuid4()),
            session_id=session_id,
            event_type=event_type,
            snapshot=snapshot,
            message=message,
            metadata=dict(metadata) if metadata else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the progress event to a clean JSON-serializable dictionary."""
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "message": self.message,
            "snapshot": self.snapshot.to_dict(),
            "metadata": dict(self.metadata),
        }
