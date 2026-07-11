# apps/data_engine/sessions/models.py
"""Domain models and DTOs for the Import Workflow & Session Management Framework.

Provides immutable Value Objects and domain entities to track the full lifecycle
of a data import session across the 10 layers of the MAC pipeline.
Strictly decoupled from Django ORM (Zero-ORM policy).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class SessionState(str, Enum):
    """Lifecycle states for an import session workflow."""
    CREATED = "CREATED"
    INGESTING = "INGESTING"
    PARSING = "PARSING"
    VALIDATING = "VALIDATING"
    MAPPING = "MAPPING"
    STAGING = "STAGING"
    RECONCILING = "RECONCILING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    PERSISTING = "PERSISTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


@dataclass(frozen=True)
class PhaseResult:
    """Immutable Value Object capturing the execution result of a single pipeline phase."""
    phase_name: str
    state: SessionState
    success: bool
    duration_ms: float
    input_record_count: int
    output_record_count: int
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportSession:
    """Domain Entity representing an active import session state and phase tracking."""
    session_id: str
    tenant_id: str
    user_id: str
    run_id: str
    state: SessionState = SessionState.CREATED
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    phases: Dict[str, PhaseResult] = field(default_factory=dict)
    total_duration_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SessionReport:
    """Immutable DTO summarizing the completed or aborted session for external consumers."""
    session_id: str
    tenant_id: str
    run_id: str
    final_state: SessionState
    total_duration_ms: float
    total_phases_executed: int
    successful_phases: int
    failed_phases: int
    phase_results: List[PhaseResult]
    error_summary: Optional[str] = None
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
