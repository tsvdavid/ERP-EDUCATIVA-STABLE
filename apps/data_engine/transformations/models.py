# apps/data_engine/transformations/models.py
"""Immutable domain models and execution DTOs for the Transformation Engine."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TransformationError:
    """Immutable model representing a validation or processor failure on a specific record."""
    error_code: str
    error_message: str
    transformation_name: str
    field_name: Optional[str] = None
    original_value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert error representation to dictionary."""
        return {
            "error_code": self.error_code,
            "error_message": self.error_message,
            "transformation_name": self.transformation_name,
            "field_name": self.field_name,
            "original_value": str(self.original_value) if self.original_value is not None else None,
        }


@dataclass(frozen=True)
class TransformationResult:
    """Immutable outcome snapshot for a single record processed through the pipeline."""
    transformed_record: Dict[str, Any]
    original_record: Dict[str, Any]
    errors: List[TransformationError] = field(default_factory=list)
    status: str = "ACCEPTED"  # ACCEPTED, REJECTED, MODIFIED, UNCHANGED

    def to_dict(self) -> Dict[str, Any]:
        """Convert result representation to dictionary."""
        return {
            "transformed_record": dict(self.transformed_record),
            "original_record": dict(self.original_record),
            "errors": [err.to_dict() for err in self.errors],
            "status": self.status,
        }


@dataclass(frozen=True)
class TransformationStatistics:
    """Performance metrics and statistical counters generated automatically by pipeline execution."""
    records_processed: int = 0
    records_accepted: int = 0
    records_rejected: int = 0
    execution_time_ms: float = 0.0
    throughput_records_per_sec: float = 0.0
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistical metrics to dictionary."""
        return {
            "records_processed": self.records_processed,
            "records_accepted": self.records_accepted,
            "records_rejected": self.records_rejected,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "throughput_records_per_sec": round(self.throughput_records_per_sec, 2),
            "error_count": self.error_count,
        }


@dataclass(frozen=True)
class TransformationReport:
    """Aggregated report detailing complete transformation pipeline execution."""
    results: List[TransformationResult] = field(default_factory=list)
    statistics: TransformationStatistics = field(default_factory=TransformationStatistics)
    errors: List[TransformationError] = field(default_factory=list)
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert complete execution report to dictionary."""
        return {
            "results": [res.to_dict() for res in self.results],
            "statistics": self.statistics.to_dict(),
            "errors": [err.to_dict() for err in self.errors],
            "success": self.success,
        }
