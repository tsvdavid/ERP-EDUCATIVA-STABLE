# apps/data_engine/application/facade.py
"""MacApplicationFacade — Unified Application Entry Point (TAREA 22).

Exposes a single, cohesive public interface encapsulating all MAC workflows,
services, and engines. External consumers interact strictly with this facade
using frozen DTOs (`dto.py`).
"""

from typing import Any, Optional

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
from .registry import ApplicationServiceRegistry


class MacApplicationFacade:
    """Central Application Facade for the MAC Engine."""

    def __init__(self, registry: Optional[ApplicationServiceRegistry] = None):
        self.registry = registry or ApplicationServiceRegistry.global_registry()

    def start_import(
        self,
        request: ImportRequest,
        step_executor: Optional[Any] = None,
    ) -> ImportResponse:
        """Start a new data import session workflow."""
        service = self.registry.get_service(BaseImportService)
        return service.start_import(request, step_executor=step_executor)

    def validate(self, request: ValidationRequest) -> ValidationResponse:
        """Validate pre-import data contracts and rules."""
        service = self.registry.get_service(BaseValidationService)
        return service.validate(request)

    def preview(self, source: Any, limit: int = 10) -> PreviewResponse:
        """Sample and inspect incoming records from a data source."""
        service = self.registry.get_service(BasePreviewService)
        return service.preview(source, limit=limit)

    def resume(self, session_id: str) -> ImportResponse:
        """Resume a paused or interrupted import workflow session."""
        service = self.registry.get_service(BaseImportService)
        return service.resume(session_id)

    def cancel(self, session_id: str) -> ImportResponse:
        """Abort or cancel an active or pending import workflow session."""
        service = self.registry.get_service(BaseImportService)
        return service.cancel(session_id)

    def export_errors(self, session_id: str, format_type: str = "csv") -> ErrorExportResponse:
        """Export rejected or error records for an import session."""
        service = self.registry.get_service(BaseExportService)
        return service.export_errors(session_id, format_type=format_type)

    def get_progress(self, session_id: str) -> ProgressResponse:
        """Retrieve real-time progress snapshot metrics."""
        service = self.registry.get_service(BaseProgressService)
        return service.get_progress(session_id)

    def get_session(self, session_id: str) -> SessionResponse:
        """Retrieve session state and phase execution summary."""
        service = self.registry.get_service(BaseSessionService)
        return service.get_session(session_id)

    def get_events(self, session_id: str, since_sequence: int = 0) -> EventListResponse:
        """Retrieve buffered event envelopes for a session from the real-time bus."""
        service = self.registry.get_service(BaseEventService)
        return service.get_events(session_id, since_sequence=since_sequence)
