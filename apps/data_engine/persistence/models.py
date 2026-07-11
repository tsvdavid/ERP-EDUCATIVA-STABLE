# apps/data_engine/persistence/models.py
"""Domain entities and data containers for the Transactional Persistence Adapter.

Defines structures for tracking individual and consolidated persistence outcomes:
- ``EntityPersistenceResult``: Detailed record of an entity's persistence in Django ORM.
- ``TransactionResult``: Consolidated result of a transactional persistence block.
- ``PersistenceContext``: Specialized container holding multi-tenant ID and resolved foreign keys.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class EntityPersistenceResult:
    """Detailed record of an entity's persistence outcome in Django ORM.

    Attributes:
        node_id: ID of the corresponding `LoadNode`.
        entity_name: Name of the persisted entity type (e.g., "Institution", "Course").
        orm_id: Real primary key or identifier resolved/assigned by Django ORM.
        created: True if the record was inserted (`create`), False if updated/matched (`find_existing`).
        success: True if the database operation succeeded without errors.
        errors: List of typed error messages in case of failure.
        duration_ms: Database execution time in milliseconds.
        timestamp: UTC ISO-8601 timestamp when persistence concluded.
    """

    node_id: str
    entity_name: str
    orm_id: Optional[str] = None
    created: bool = False
    success: bool = True
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class TransactionResult:
    """Consolidated outcome of a transactional persistence operation.

    Attributes:
        success: True if the atomic block committed successfully.
        entity_result: Optional `EntityPersistenceResult` detailing the specific entity operation.
        error_type: Optional exception category ("IntegrityError", "ValidationError", "ProtectedError", etc.).
        error_message: Detailed diagnostic error message if `success` is False.
    """

    success: bool
    entity_result: Optional[EntityPersistenceResult] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class PersistenceContext:
    """Specialized context container passed down to concrete ORM repositories.

    Enforces multi-tenant isolation (`tenant_id`) and provides resolved foreign
    key instances or database identifiers (`resolved_dependencies`) needed for FK links.

    Attributes:
        tenant_id: Institutional tenant identifier (`institution_id`).
        resolved_dependencies: Mapping of prerequisite `node_id` strings to resolved ORM instances or PKs.
        is_dry_run: Flag indicating if the persistence should be rolled back after execution.
        extra_metadata: Optional dictionary of additional execution metadata.
    """

    tenant_id: str
    resolved_dependencies: Dict[str, Any] = field(default_factory=dict)
    is_dry_run: bool = False
    extra_metadata: Dict[str, Any] = field(default_factory=dict)


__all__ = [
    "EntityPersistenceResult",
    "TransactionResult",
    "PersistenceContext",
]
