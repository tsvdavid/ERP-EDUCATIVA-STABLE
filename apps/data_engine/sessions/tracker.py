# apps/data_engine/sessions/tracker.py
"""SessionTracker Finite State Machine and Phase Metrics Tracker.

Manages the valid state transitions and monotonic duration tracking across the
10 pipeline phases of an import session without external ORM dependencies.
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from .base import BaseSessionTracker
from .models import ImportSession, PhaseResult, SessionReport, SessionState


class InvalidSessionStateTransitionError(Exception):
    """Raised when an illegal lifecycle state transition is attempted on a session."""
    pass


class SessionTracker(BaseSessionTracker):
    """Concrete state machine and metrics tracker for an ImportSession."""

    # Ordered sequence of lifecycle phases from creation to completion
    _PHASE_ORDER: List[SessionState] = [
        SessionState.CREATED,
        SessionState.INGESTING,
        SessionState.PARSING,
        SessionState.VALIDATING,
        SessionState.MAPPING,
        SessionState.STAGING,
        SessionState.RECONCILING,
        SessionState.PLANNING,
        SessionState.EXECUTING,
        SessionState.PERSISTING,
        SessionState.COMPLETED,
    ]

    def __init__(self, session: ImportSession):
        if not isinstance(session, ImportSession):
            raise TypeError("session must be an instance of ImportSession")
        self._session = session

    @property
    def session(self) -> ImportSession:
        return self._session

    def can_transition_to(self, next_state: SessionState) -> bool:
        if not isinstance(next_state, SessionState):
            return False
        current_state = self._session.state
        if current_state == next_state:
            return True
        if current_state in (SessionState.COMPLETED, SessionState.FAILED, SessionState.ABORTED):
            return False
        if next_state in (SessionState.FAILED, SessionState.ABORTED):
            return True
        valid_map = {
            SessionState.CREATED: {SessionState.INGESTING},
            SessionState.INGESTING: {SessionState.PARSING},
            SessionState.PARSING: {
                SessionState.VALIDATING, SessionState.MAPPING, SessionState.STAGING,
                SessionState.RECONCILING, SessionState.PLANNING, SessionState.EXECUTING,
            },
            SessionState.VALIDATING: {
                SessionState.MAPPING, SessionState.STAGING,
                SessionState.RECONCILING, SessionState.PLANNING, SessionState.EXECUTING,
            },
            SessionState.MAPPING: {
                SessionState.STAGING, SessionState.RECONCILING,
                SessionState.PLANNING, SessionState.EXECUTING,
            },
            SessionState.STAGING: {
                SessionState.RECONCILING, SessionState.PLANNING, SessionState.EXECUTING,
            },
            SessionState.RECONCILING: {SessionState.PLANNING, SessionState.EXECUTING},
            SessionState.PLANNING: {SessionState.EXECUTING},
            SessionState.EXECUTING: {SessionState.PERSISTING, SessionState.COMPLETED},
            SessionState.PERSISTING: {SessionState.COMPLETED},
        }
        allowed = valid_map.get(current_state, set())
        return next_state in allowed

    def transition_to(self, next_state: SessionState) -> None:
        if not isinstance(next_state, SessionState):
            raise TypeError(f"Invalid state type: {type(next_state)}")
        if self._session.state == next_state:
            return
        if not self.can_transition_to(next_state):
            raise InvalidSessionStateTransitionError(
                f"Illegal transition from '{self._session.state.value}' to '{next_state.value}'"
            )
        self._session.state = next_state
        self._session.updated_at = datetime.now(timezone.utc).isoformat()

    def start_phase(self, phase_name: str, target_state: SessionState) -> float:
        if not phase_name:
            raise ValueError("phase_name must be a non-empty string")
        self.transition_to(target_state)
        return time.monotonic()

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
        if not phase_name:
            raise ValueError("phase_name must be a non-empty string")
        duration_ms = max(0.0, (time.monotonic() - start_time) * 1000.0)
        errs = list(errors) if errors else []
        meta = dict(metadata) if metadata else {}

        self._session.total_duration_ms += duration_ms
        self._session.updated_at = datetime.now(timezone.utc).isoformat()

        if not success and errs:
            if not self._session.error_message:
                self._session.error_message = f"Phase '{phase_name}' failed: {errs[0]}"

        phase_res = PhaseResult(
            phase_name=phase_name,
            state=self._session.state,
            success=success,
            duration_ms=duration_ms,
            input_record_count=input_count,
            output_record_count=output_count,
            errors=errs,
            metadata=meta,
        )
        self._session.phases[phase_name] = phase_res
        return phase_res

    def abort_session(self, reason: str, target_state: SessionState = SessionState.FAILED) -> None:
        if target_state not in (SessionState.FAILED, SessionState.ABORTED):
            raise ValueError("target_state for abort must be FAILED or ABORTED")
        if self.can_transition_to(target_state):
            self._session.state = target_state
        self._session.error_message = reason
        self._session.updated_at = datetime.now(timezone.utc).isoformat()

    def build_report(self, context_snapshot: Optional[Dict[str, Any]] = None) -> SessionReport:
        phase_results = list(self._session.phases.values())
        successful_phases = sum(1 for p in phase_results if p.success)
        failed_phases = sum(1 for p in phase_results if not p.success)

        return SessionReport(
            session_id=self._session.session_id,
            tenant_id=self._session.tenant_id,
            run_id=self._session.run_id,
            final_state=self._session.state,
            total_duration_ms=self._session.total_duration_ms,
            total_phases_executed=len(phase_results),
            successful_phases=successful_phases,
            failed_phases=failed_phases,
            phase_results=phase_results,
            error_summary=self._session.error_message,
            context_snapshot=dict(context_snapshot) if context_snapshot else {},
        )
