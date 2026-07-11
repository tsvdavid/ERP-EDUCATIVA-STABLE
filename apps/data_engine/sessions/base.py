# apps/data_engine/sessions/base.py
"""Abstract contracts for the Import Workflow & Session Management Framework.

Defines the interfaces required for state tracking and orchestration across
the 10 layers of the MAC pipeline without tying to specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .models import ImportSession, PhaseResult, SessionReport, SessionState


class BaseSessionTracker(ABC):
    """Abstract contract for tracking session state transitions and phase metrics."""

    @property
    @abstractmethod
    def session(self) -> ImportSession:
        """Return the underlying active ImportSession entity."""
        raise NotImplementedError

    @abstractmethod
    def can_transition_to(self, next_state: SessionState) -> bool:
        """Check whether transitioning from the current state to next_state is valid."""
        raise NotImplementedError

    @abstractmethod
    def transition_to(self, next_state: SessionState) -> None:
        """Transition the session state to next_state or raise InvalidSessionStateTransitionError."""
        raise NotImplementedError

    @abstractmethod
    def start_phase(self, phase_name: str, target_state: SessionState) -> float:
        """Begin tracking a pipeline phase, transitioning state and returning start timestamp (monotonic)."""
        raise NotImplementedError

    @abstractmethod
    def end_phase(
        self,
        phase_name: str,
        start_time: float,
        success: bool,
        input_count: int,
        output_count: int,
        errors: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PhaseResult:
        """End tracking a pipeline phase, recording metrics and duration."""
        raise NotImplementedError

    @abstractmethod
    def abort_session(self, reason: str, target_state: SessionState = SessionState.FAILED) -> None:
        """Immediately abort or fail the session with a specific reason."""
        raise NotImplementedError

    @abstractmethod
    def build_report(self, context_snapshot: Optional[Dict[str, Any]] = None) -> SessionReport:
        """Construct and return an immutable SessionReport DTO."""
        raise NotImplementedError


class BaseWorkflowOrchestrator(ABC):
    """Abstract contract for orchestrating the multi-layer MAC import pipeline."""

    @abstractmethod
    def run_workflow(
        self,
        tenant_id: str,
        user_id: str,
        source: Any,
        pipeline_config: Dict[str, Any],
        run_id: Optional[str] = None,
        is_dry_run: bool = False,
    ) -> SessionReport:
        """Execute the full 10-layer import workflow and return the immutable report."""
        raise NotImplementedError
