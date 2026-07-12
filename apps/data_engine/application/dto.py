# apps/data_engine/application/dto.py
"""Immutable Data Transfer Objects (DTOs) for the MAC Application Layer.

All communication across the Application boundary (both inputs and outputs)
MUST use these frozen dataclasses. Never return Django ORM models, query
results, or un-contracted arbitrary dictionaries.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ImportRequest:
    """Immutable input contract to initiate or configure an import workflow."""
    tenant_id: str
    user_id: str
    source: Any
    pipeline_config: Dict[str, Any]
    run_id: Optional[str] = None
    is_dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean dictionary representation."""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "source": str(self.source) if not isinstance(self.source, (dict, list)) else self.source,
            "pipeline_config": dict(self.pipeline_config),
            "run_id": self.run_id,
            "is_dry_run": self.is_dry_run,
        }


@dataclass(frozen=True)
class ImportResponse:
    """Immutable output contract representing the outcome or status of an import run."""
    session_id: str
    run_id: str
    state: str
    total_records: int
    processed_records: int
    errors: List[str] = field(default_factory=list)
    is_success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean dictionary representation."""
        return {
            "session_id": self.session_id,
            "run_id": self.run_id,
            "state": self.state,
            "total_records": self.total_records,
            "processed_records": self.processed_records,
            "errors": list(self.errors),
            "is_success": self.is_success,
        }


@dataclass(frozen=True)
class ValidationRequest:
    """Immutable input contract for pre-import data or rule validation."""
    tenant_id: str
    source: Any
    rules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean dictionary representation."""
        return {
            "tenant_id": self.tenant_id,
            "source": str(self.source) if not isinstance(self.source, (dict, list)) else self.source,
            "rules": list(self.rules),
        }


@dataclass(frozen=True)
class ValidationResponse:
    """Immutable output contract returning validation inspection results."""
    is_valid: bool
    total_checked: int
    violations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "total_checked": self.total_checked,
            "violations": [dict(v) for v in self.violations],
        }


@dataclass(frozen=True)
class ProgressResponse:
    """Immutable output contract representing real-time session progress metrics."""
    session_id: str
    run_id: str
    state: str
    current_phase: str
    percentage: float
    processed: int
    total: int
    accepted: int
    rejected: int
    elapsed_ms: float
    eta_seconds: float
    throughput: float

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean dictionary representation."""
        return {
            "session_id": self.session_id,
            "run_id": self.run_id,
            "state": self.state,
            "current_phase": self.current_phase,
            "percentage": self.percentage,
            "processed": self.processed,
            "total": self.total,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "elapsed_ms": self.elapsed_ms,
            "eta_seconds": self.eta_seconds,
            "throughput": self.throughput,
        }


@dataclass(frozen=True)
class SessionResponse:
    """Immutable output contract summarizing an import session's lifecycle and phase history."""
    session_id: str
    tenant_id: str
    user_id: str
    state: str
    phases: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean dictionary representation."""
        return {
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "state": self.state,
            "phases": [dict(p) for p in self.phases],
        }


@dataclass(frozen=True)
class PreviewResponse:
    """Immutable output contract containing a sample preview of incoming records."""
    headers: List[str]
    sample_rows: List[Dict[str, Any]]
    total_preview_records: int

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean dictionary representation."""
        return {
            "headers": list(self.headers),
            "sample_rows": [dict(r) for r in self.sample_rows],
            "total_preview_records": self.total_preview_records,
        }


@dataclass(frozen=True)
class ErrorExportResponse:
    """Immutable output contract containing exported error records or rejection reports."""
    session_id: str
    export_format: str
    data: bytes
    error_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean dictionary representation without binary data payload."""
        return {
            "session_id": self.session_id,
            "export_format": self.export_format,
            "error_count": self.error_count,
            "data_length_bytes": len(self.data),
        }


@dataclass(frozen=True)
class EventListResponse:
    """Immutable output contract returning a replay buffer slice of session events."""
    session_id: str
    events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean dictionary representation."""
        return {
            "session_id": self.session_id,
            "events": [dict(e) for e in self.events],
        }
