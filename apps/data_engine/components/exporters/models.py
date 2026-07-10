# apps/data_engine/components/exporters/models.py
"""Domain entities for the MAC Export Engine.

Defines the data structures used to represent export operations:

- ``ExportFormat``: Enum of supported output target formats.
- ``ExportStatus``: Enum of lifecycle states for an export item.
- ``ExportItem``: A single record or data unit ready for export.
- ``ExportBatch``: A group of items forming an atomic export unit.
- ``ExportResult``: Consolidated outcome of an export strategy execution.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ExportFormat(str, Enum):
    """Supported output formats for the Export Engine.

    These values determine how the BaseOutputFormatter structures the data.
    """

    CSV = "CSV"
    EXCEL = "EXCEL"
    JSON = "JSON"
    API_PAYLOAD = "API_PAYLOAD"
    S3_OBJECT = "S3_OBJECT"
    QUEUE_MESSAGE = "QUEUE_MESSAGE"
    ERP_SYNC = "ERP_SYNC"
    CUSTOM = "CUSTOM"


class ExportStatus(str, Enum):
    """Lifecycle states for an export item."""

    PENDING = "PENDING"
    FORMATTING = "FORMATTING"
    DISPATCHED = "DISPATCHED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class ExportItem:
    """Represents a single record prepared for export.

    Attributes:
        item_id: Unique identifier (auto-generated UUID4).
        record_id: Reference to originating StagingRecord/ImportItem/Payload ID.
        tenant_id: Tenant that owns this record (multi-tenant isolation).
        payload: The dictionary of data to format and export.
        status: Current lifecycle status (default: PENDING).
        error: Error message if the export failed (default: None).
    """

    record_id: str
    tenant_id: str
    payload: Dict[str, Any]
    status: ExportStatus = ExportStatus.PENDING
    error: Optional[str] = None
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ExportBatch:
    """Groups export items into an atomic export unit for a destination/format.

    Attributes:
        batch_id: Unique identifier (auto-generated UUID4).
        tenant_id: Tenant that owns this batch.
        run_id: Pipeline run identifier for traceability.
        format: Target format requested (default: JSON).
        destination: Logical URI or destination target (e.g., "memory://export").
        items: List of ExportItem instances in this batch.
        metadata: Additional export parameters or configuration options.
    """

    tenant_id: str
    run_id: str
    items: List[ExportItem] = field(default_factory=list)
    format: ExportFormat = ExportFormat.JSON
    destination: str = "memory://default"
    metadata: Dict[str, Any] = field(default_factory=dict)
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ExportResult:
    """Consolidated outcome of an export strategy execution.

    Attributes:
        batch_id: Reference to the processed batch.
        format: Format processed.
        destination: Destination where output was dispatched or simulated.
        total_items: Total number of items processed.
        exported_count: Items with status COMPLETED.
        failed_count: Items with status FAILED.
        success: True if all items resulted in COMPLETED.
        items: Items with updated status post-execution.
        output_payload: The structured result produced (dict/string/metadata).
        errors: Detailed error list for failed items.
    """

    batch_id: str
    format: ExportFormat
    destination: str
    total_items: int
    exported_count: int
    failed_count: int
    success: bool = True
    items: List[ExportItem] = field(default_factory=list)
    output_payload: Any = None
    errors: List[Dict[str, Any]] = field(default_factory=list)


__all__ = [
    "ExportFormat",
    "ExportStatus",
    "ExportItem",
    "ExportBatch",
    "ExportResult",
]
