# apps/data_engine/components/staging/models.py
"""Domain entities for the MAC Staging Engine.

Defines the data structures used to represent processed records
in the staging boundary, before optional persistence to the ERP.

- ``StagingStatus``: Enum of lifecycle states for a record.
- ``StagingRecord``: Immutable dataclass representing a single staged row.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class StagingStatus(str, Enum):
    """Lifecycle states for a staging record.

    In TAREA 12 only VALIDATED and REJECTED are actively used.
    The remaining states are declared for future phases.
    """

    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    READY_IMPORT = "READY_IMPORT"
    IMPORTED = "IMPORTED"
    FAILED = "FAILED"


@dataclass
class StagingRecord:
    """Represents a single row processed by the MAC pipeline.

    Attributes:
        record_id: Unique identifier (auto-generated UUID4).
        tenant_id: Tenant that owns this record.
        run_id: Identifier of the pipeline execution that produced this record.
        row_index: Original row position in the source data.
        payload: The mapped and typed data for this row.
        status: Current lifecycle status.
        errors: Validation errors associated with this row (empty if VALIDATED).
    """

    tenant_id: str
    run_id: str
    row_index: int
    payload: Dict[str, Any]
    status: StagingStatus = StagingStatus.RECEIVED
    errors: List[Dict[str, Any]] = field(default_factory=list)
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))


__all__ = ["StagingStatus", "StagingRecord"]
