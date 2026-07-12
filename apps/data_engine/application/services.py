# apps/data_engine/application/services.py
"""Concrete Application Layer Services (TAREA 22).

Implementations of the abstract application service contracts. Encapsulates
the underlying MAC engines (`components/`, `sessions/`, `progress/`, `events/`,
`persistence/`) and returns strictly frozen DTO contracts (`dto.py`).
"""

import json
import uuid
from typing import Any, Dict, List, Optional

from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.events.dispatcher import EventBusBridgeObserver
from apps.data_engine.events.registry import EventBusRegistry
from apps.data_engine.progress.registry import ProgressRegistry
from apps.data_engine.progress.tracker import ProgressTracker
from apps.data_engine.sessions.models import SessionReport, SessionState
from apps.data_engine.sessions.orchestrator import ImportWorkflowOrchestrator

from .contracts import (
    BaseEventService,
    BaseExportService,
    BaseImportService,
    BasePreviewService,
    BaseProgressService,
    BaseSessionService,
    BaseValidationService,
)
from .dto import (
    ErrorExportResponse,
    EventListResponse,
    ImportRequest,
    ImportResponse,
    PreviewResponse,
    ProgressResponse,
    SessionResponse,
    ValidationRequest,
    ValidationResponse,
)
from .exceptions import ImportException, SessionException, ValidationException


# Shared in-memory session report store across services (Zero-ORM session storage)
_SESSION_STORE: Dict[str, SessionReport] = {}
_RUN_TO_SESSION: Dict[str, str] = {}


class ImportService(BaseImportService):
    """Orchestrates import sessions across all 10 MAC layers."""

    def __init__(self, registry: Optional[MacRegistry] = None):
        self.registry = registry or MacRegistry.global_registry()

    def start_import(
        self,
        request: ImportRequest,
        step_executor: Optional[Any] = None,
    ) -> ImportResponse:
        """Start a new import workflow session."""
        if not request.tenant_id or not request.user_id:
            raise ImportException("tenant_id and user_id are required in ImportRequest")

        run_id = request.run_id or str(uuid.uuid4())

        # Ensure ProgressTracker is registered and bridged to the central EventBus
        tracker = ProgressRegistry.global_registry().get(run_id)
        if tracker is None:
            # Estimate or default expected records for progress initialization
            tracker = ProgressTracker(run_id, total_expected_records=100)
            ProgressRegistry.global_registry().register(run_id, tracker)

        dispatcher = EventBusRegistry.global_registry().get_dispatcher()
        bridge = EventBusBridgeObserver(dispatcher)
        tracker.subscribe(bridge)

        tracker.record_session_start()
        tracker.record_phase_start("Workflow")

        orchestrator = ImportWorkflowOrchestrator(
            step_executor=step_executor,
            registry=self.registry,
        )

        try:
            report = orchestrator.run_workflow(
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                source=request.source,
                pipeline_config=request.pipeline_config,
                run_id=run_id,
                is_dry_run=request.is_dry_run,
            )
            _SESSION_STORE[report.session_id] = report
            _RUN_TO_SESSION[run_id] = report.session_id

            is_success = report.final_state in (
                SessionState.COMPLETED,
                SessionState.INGESTING,
                SessionState.PARSING,
                SessionState.VALIDATING,
                SessionState.MAPPING,
                SessionState.STAGING,
                SessionState.RECONCILING,
                SessionState.PLANNING,
                SessionState.EXECUTING,
                SessionState.PERSISTING,
            )
            errors = [err for p in report.phase_results for err in p.errors]
            if report.error_summary and report.error_summary not in errors:
                errors.append(report.error_summary)
            if not is_success and not errors:
                errors.append(f"Session terminated with state {report.final_state.value}")

            processed = max([p.output_record_count for p in report.phase_results] or [0])
            tracker.record_phase_progress("Workflow", processed=processed, accepted=processed)
            tracker.record_session_end(report.final_state.value)

            return ImportResponse(
                session_id=report.session_id,
                run_id=report.run_id,
                state=report.final_state.value,
                total_records=processed,
                processed_records=processed,
                errors=errors,
                is_success=is_success,
            )
        except Exception as exc:
            tracker.record_session_end(SessionState.FAILED.value)
            raise ImportException(f"Import workflow failed: {exc}") from exc

    def resume(self, session_id: str) -> ImportResponse:
        """Resume an existing paused or interrupted session."""
        report = _SESSION_STORE.get(session_id)
        if not report:
            raise SessionException(f"Cannot resume: Session '{session_id}' not found in session store")

        if report.final_state == SessionState.ABORTED:
            raise ImportException(f"Cannot resume session in terminal state {report.final_state.value}")

        processed = max([p.output_record_count for p in report.phase_results] or [0])
        return ImportResponse(
            session_id=report.session_id,
            run_id=report.run_id,
            state="RESUMED",
            total_records=processed,
            processed_records=processed,
            errors=[],
            is_success=True,
        )

    def cancel(self, session_id: str) -> ImportResponse:
        """Cancel/Abort an active session."""
        report = _SESSION_STORE.get(session_id)
        if not report:
            raise SessionException(f"Cannot cancel: Session '{session_id}' not found in session store")

        # Update in-memory tracker if active
        tracker = ProgressRegistry.global_registry().get(report.run_id)
        if tracker:
            tracker.record_session_end("ABORTED")

        processed = max([p.output_record_count for p in report.phase_results] or [0])
        return ImportResponse(
            session_id=report.session_id,
            run_id=report.run_id,
            state="ABORTED",
            total_records=processed,
            processed_records=processed,
            errors=["Session explicitly cancelled via application service"],
            is_success=False,
        )


class ValidationService(BaseValidationService):
    """Executes pre-import validation checks and rule inspections."""

    def __init__(self, registry: Optional[MacRegistry] = None):
        self.registry = registry or MacRegistry.global_registry()

    def validate(self, request: ValidationRequest) -> ValidationResponse:
        """Validate source data against specified component rules without running full import."""
        if not request.tenant_id:
            raise ValidationException("tenant_id is required for validation")

        violations: List[Dict[str, Any]] = []
        total_checked = 0

        # If rules list provided, execute validator components from registry
        for rule_name in request.rules:
            try:
                comp = self.registry.get(rule_name)
                ctx = {"source": request.source, "tenant_id": request.tenant_id, "payload": {}}
                res = comp.execute(ctx)
                if isinstance(res, dict) and "errors" in res:
                    for err in res["errors"]:
                        violations.append({"rule": rule_name, "error": str(err)})
                total_checked += 1
            except Exception as exc:
                violations.append({"rule": rule_name, "error": f"Validation execution failure: {exc}"})
                total_checked += 1

        is_valid = len(violations) == 0
        return ValidationResponse(
            is_valid=is_valid,
            total_checked=total_checked,
            violations=violations,
        )


class PreviewService(BasePreviewService):
    """Provides sample preview inspecting records from data sources."""

    def __init__(self, registry: Optional[MacRegistry] = None):
        self.registry = registry or MacRegistry.global_registry()

    def preview(self, source: Any, limit: int = 10) -> PreviewResponse:
        """Inspect and return sample rows up to `limit`."""
        if limit <= 0:
            limit = 10

        rows: List[Dict[str, Any]] = []
        headers: List[str] = []

        if isinstance(source, list):
            sample = source[:limit]
            for idx, item in enumerate(sample):
                if isinstance(item, dict):
                    if not headers:
                        headers = list(item.keys())
                    rows.append(dict(item))
                else:
                    if not headers:
                        headers = ["value"]
                    rows.append({"value": item})
            return PreviewResponse(
                headers=headers,
                sample_rows=rows,
                total_preview_records=len(rows),
            )
        elif isinstance(source, dict):
            headers = list(source.keys())
            rows.append(dict(source))
            return PreviewResponse(
                headers=headers,
                sample_rows=rows,
                total_preview_records=1,
            )
        else:
            # Fallback or external string/source representation
            headers = ["source_preview"]
            rows.append({"source_preview": str(source)[:200]})
            return PreviewResponse(
                headers=headers,
                sample_rows=rows,
                total_preview_records=1,
            )


class ExportService(BaseExportService):
    """Generates exports of errors, rejections, or session data."""

    def export_errors(self, session_id: str, format_type: str = "csv") -> ErrorExportResponse:
        """Generate error export payload for a session."""
        report = _SESSION_STORE.get(session_id)
        errors: List[str] = []
        if report:
            errors = [err for p in report.phase_results for err in p.errors]
            if report.error_summary and report.error_summary not in errors:
                errors.append(report.error_summary)
        else:
            # Try finding via run_id or return empty if not found
            for rep in _SESSION_STORE.values():
                if rep.run_id == session_id:
                    errors = [err for p in rep.phase_results for err in p.errors]
                    if rep.error_summary and rep.error_summary not in errors:
                        errors.append(rep.error_summary)
                    break

        format_type = format_type.lower()
        if format_type == "json":
            payload = json.dumps({"session_id": session_id, "errors": errors}, ensure_ascii=False).encode("utf-8")
        else:
            # Default to CSV format
            lines = ["error_message"]
            for err in errors:
                lines.append(f'"{err.replace('"', '""')}"')
            payload = "\n".join(lines).encode("utf-8")

        return ErrorExportResponse(
            session_id=session_id,
            export_format=format_type,
            data=payload,
            error_count=len(errors),
        )


class ProgressService(BaseProgressService):
    """Retrieves real-time session progress snapshots."""

    def get_progress(self, session_id: str) -> ProgressResponse:
        """Retrieve current real-time progress metrics."""
        # Check by run_id or resolved run_id from session_id
        run_id = session_id
        if session_id in _SESSION_STORE:
            run_id = _SESSION_STORE[session_id].run_id
        elif session_id in _RUN_TO_SESSION:
            pass

        tracker = ProgressRegistry.global_registry().get(run_id)
        if tracker is None:
            # Also check if session_id is directly registered
            tracker = ProgressRegistry.global_registry().get(session_id)

        if tracker is None:
            raise SessionException(f"No active progress tracking found for session '{session_id}'")

        snapshot = tracker.get_snapshot()
        return ProgressResponse(
            session_id=session_id,
            run_id=snapshot.run_id,
            state=snapshot.state,
            current_phase=snapshot.current_phase,
            percentage=snapshot.overall_percentage,
            processed=snapshot.records_processed,
            total=snapshot.total_records_expected,
            accepted=snapshot.records_accepted,
            rejected=snapshot.records_rejected,
            elapsed_ms=snapshot.elapsed_duration_ms,
            eta_seconds=snapshot.estimated_eta_seconds,
            throughput=snapshot.throughput_records_sec,
        )


class SessionService(BaseSessionService):
    """Queries session state summaries and lifecycle phase execution reports."""

    def get_session(self, session_id: str) -> SessionResponse:
        """Retrieve state and phase summary for an import session."""
        report = _SESSION_STORE.get(session_id)
        if not report:
            # Check if run_id was passed instead
            if session_id in _RUN_TO_SESSION:
                report = _SESSION_STORE.get(_RUN_TO_SESSION[session_id])

        if not report:
            raise SessionException(f"Session '{session_id}' not found in session store")

        phases: List[Dict[str, Any]] = []
        for p in report.phase_results:
            phases.append({
                "phase_name": p.phase_name,
                "success": p.success,
                "input_records": p.input_record_count,
                "output_records": p.output_record_count,
                "duration_ms": p.duration_ms,
                "errors": list(p.errors),
            })

        return SessionResponse(
            session_id=report.session_id,
            tenant_id=report.tenant_id,
            user_id=report.context_snapshot.get("user_id", ""),
            state=report.final_state.value,
            phases=phases,
        )


class EventService(BaseEventService):
    """Retrieves buffered real-time event envelopes from the Event Bus."""

    def get_events(self, session_id: str, since_sequence: int = 0) -> EventListResponse:
        """Retrieve buffered event envelopes for a session."""
        dispatcher = EventBusRegistry.global_registry().get_dispatcher()
        # Replay checks the buffer by session_id (which could be run_id or session_id)
        envelopes = dispatcher.replay(session_id, since_sequence=since_sequence)
        if not envelopes and session_id in _SESSION_STORE:
            # Also try replay with run_id if session_id passed
            run_id = _SESSION_STORE[session_id].run_id
            if run_id != session_id:
                envelopes = dispatcher.replay(run_id, since_sequence=since_sequence)

        return EventListResponse(
            session_id=session_id,
            events=[e.to_dict() for e in envelopes],
        )
