# apps/data_engine/integration/dto.py
"""Immutable DTOs for ERP Integration Layer."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class EntityMapping:
    """Represents a configuration of how a source field maps to an ERP entity target field."""
    source_field: str
    target_field: str
    converter_name: Optional[str] = None
    default_value: Optional[Any] = None


@dataclass(frozen=True)
class PersistenceRequest:
    """Represents a request to persist records of a specific entity in the ERP."""
    entity_name: str
    records: List[Dict[str, Any]]
    mappings: List[EntityMapping] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PersistenceResult:
    """Represents the outcome of persisting a single entity record."""
    success: bool
    record_id: Optional[str] = None
    error_message: Optional[str] = None
    created: bool = False
    original_data: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class RejectedRecord:
    """Represents a record that failed validation or writing in the persistence adapter."""
    record: Dict[str, Any]
    reason: str
    error_type: str = "PERSISTENCE"


@dataclass(frozen=True)
class BatchPersistenceResult:
    """Summarizes the outcome of a batch persistence process."""
    processed_count: int
    success_count: int
    failed_count: int
    results: List[PersistenceResult] = field(default_factory=list)
    rejected_records: List[RejectedRecord] = field(default_factory=list)
