# apps/data_engine/application/contracts.py
"""Abstract service contracts for the MAC Application Layer.

Enforces Dependency Inversion across all application use cases. Every service
and facade interacts solely through these abstract definitions.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

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


class BaseApplicationService(ABC):
    """Abstract base contract for all MAC application services."""
    pass


class BaseImportService(BaseApplicationService):
    """Contract for managing data import sessions and execution workflows."""

    @abstractmethod
    def start_import(
        self,
        request: ImportRequest,
        step_executor: Optional[Any] = None,
    ) -> ImportResponse:
        """Initiate and run a new import workflow session."""
        raise NotImplementedError

    @abstractmethod
    def resume(self, session_id: str) -> ImportResponse:
        """Resume a paused or interrupted import workflow session."""
        raise NotImplementedError

    @abstractmethod
    def cancel(self, session_id: str) -> ImportResponse:
        """Abort an active or pending import workflow session."""
        raise NotImplementedError


class BaseValidationService(BaseApplicationService):
    """Contract for pre-import validation and schema checking."""

    @abstractmethod
    def validate(self, request: ValidationRequest) -> ValidationResponse:
        """Validate source data against specified rules without importing."""
        raise NotImplementedError


class BasePreviewService(BaseApplicationService):
    """Contract for sampling and previewing incoming data sources."""

    @abstractmethod
    def preview(self, source: Any, limit: int = 10) -> PreviewResponse:
        """Inspect and return a sample of records from the source."""
        raise NotImplementedError


class BaseExportService(BaseApplicationService):
    """Contract for generating data or error exports from session runs."""

    @abstractmethod
    def export_errors(self, session_id: str, format_type: str = "csv") -> ErrorExportResponse:
        """Generate an export payload of failed or rejected records for a session."""
        raise NotImplementedError


class BaseProgressService(BaseApplicationService):
    """Contract for retrieving real-time metrics and progress snapshots."""

    @abstractmethod
    def get_progress(self, session_id: str) -> ProgressResponse:
        """Retrieve the current real-time progress metrics for a session."""
        raise NotImplementedError


class BaseSessionService(BaseApplicationService):
    """Contract for querying import session lifecycle state and history."""

    @abstractmethod
    def get_session(self, session_id: str) -> SessionResponse:
        """Retrieve state and phase summary for an import session."""
        raise NotImplementedError


class BaseEventService(BaseApplicationService):
    """Contract for retrieving event stream replay histories."""

    @abstractmethod
    def get_events(self, session_id: str, since_sequence: int = 0) -> EventListResponse:
        """Retrieve buffered event envelopes for a session from the event bus."""
        raise NotImplementedError
