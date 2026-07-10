# apps/data_engine/components/importers/models.py
"""Domain entities for the MAC Import Engine.

Defines the data structures used to represent import operations:

- ``ImportStatus``: Enum of lifecycle states for an import item.
- ``ImportItem``: A single record ready for import.
- ``ImportBatch``: A group of items forming an atomic import unit.
- ``ImportResult``: Consolidated outcome of an import strategy execution.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ImportStatus(str, Enum):
    """Lifecycle states for an import item.

    In TAREA 13, DryRunStrategy transitions items from PENDING to SUCCESS.
    FAILED and SKIPPED are declared for future strategies.
    """

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class ImportItem:
    """Represents a single record ready for import.

    Attributes:
        item_id: Unique identifier (auto-generated UUID4).
        record_id: Reference to the originating StagingRecord.record_id.
        tenant_id: Tenant that owns this record.
        payload: The validated and typed data for this row.
        status: Current import status (default: PENDING).
        error: Error message if the import failed (default: None).
    """

    record_id: str
    tenant_id: str
    payload: Dict[str, Any]
    status: ImportStatus = ImportStatus.PENDING
    error: Optional[str] = None
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ImportBatch:
    """Groups import items into an atomic import unit.

    Attributes:
        batch_id: Unique identifier (auto-generated UUID4).
        tenant_id: Tenant that owns this batch.
        run_id: Pipeline run identifier for traceability.
        items: List of ImportItem instances in this batch.
        target_entity: Conceptual name of the destination entity
                       (e.g., "students", "grades"). Default: "unknown".
    """

    tenant_id: str
    run_id: str
    items: List[ImportItem] = field(default_factory=list)
    target_entity: str = "unknown"
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ImportResult:
    """Consolidated outcome of an import strategy execution.

    Attributes:
        batch_id: Reference to the processed batch.
        success: True if all items resulted in SUCCESS.
        total_items: Total number of items processed.
        success_count: Items with status SUCCESS.
        failed_count: Items with status FAILED.
        skipped_count: Items with status SKIPPED.
        items: Items with updated status post-execution.
        errors: Detailed error list for failed items.
    """

    batch_id: str
    total_items: int
    success_count: int
    failed_count: int
    skipped_count: int
    success: bool = True
    items: List[ImportItem] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)


__all__ = ["ImportStatus", "ImportItem", "ImportBatch", "ImportResult"]
