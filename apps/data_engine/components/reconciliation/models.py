# apps/data_engine/components/reconciliation/models.py
"""Domain entities for the MAC Reconciliation, Lineage & Audit Engine.

Defines the data structures used for pipeline monitoring and audit trails:

- ``ReconciliationStatus``: Enum representing the quantitative balance and integrity state of the pipeline run.
- ``StageMetric``: Quantitative metrics audited for a single pipeline stage.
- ``LineageRecord``: End-to-end traceability of a single record ID across all pipeline layers.
- ``PipelineManifest``: Immutable audit manifest consolidating metrics, lineage, and multi-tenant isolation verification.
"""

import datetime
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ReconciliationStatus(str, Enum):
    """Lifecycle and audit balance states for the pipeline reconciliation."""

    BALANCED = "BALANCED"
    DISCREPANCY_DETECTED = "DISCREPANCY_DETECTED"
    CRITICAL_DROP = "CRITICAL_DROP"
    UNPROCESSED = "UNPROCESSED"


@dataclass
class StageMetric:
    """Quantitative metrics audited for an individual stage of the pipeline.

    Attributes:
        stage_name: Name of the pipeline stage (e.g., 'mapping', 'staging', 'import').
        items_in: Number of records entering the stage.
        items_out: Number of records successfully output from the stage.
        items_rejected: Number of records rejected or failed in the stage.
        conversion_rate_pct: Percentage of records successfully output relative to input.
    """

    stage_name: str
    items_in: int
    items_out: int
    items_rejected: int
    conversion_rate_pct: float = 0.0

    def __post_init__(self):
        if self.conversion_rate_pct == 0.0 and self.items_in > 0:
            self.conversion_rate_pct = round(
                (self.items_out / self.items_in) * 100.0, 2
            )


@dataclass
class LineageRecord:
    """End-to-end traceability of a specific record across the 8 MAC layers.

    Attributes:
        record_id: Unique identifier tracing the record back to its source.
        tenant_id: Tenant/Institution owning this record.
        stage_history: List of stage names this record traversed.
        final_status: Last known status (e.g., 'SUCCESS', 'VALIDATED', 'FAILED').
        accumulated_errors: All validation or processing errors encountered by this record.
    """

    record_id: str
    tenant_id: str
    stage_history: List[str] = field(default_factory=list)
    final_status: str = "UNKNOWN"
    accumulated_errors: List[str] = field(default_factory=list)


@dataclass
class PipelineManifest:
    """Immutable audit manifest summarizing a MAC pipeline execution.

    Consolidates stage metrics, lineage summary, discrepancies, and isolation checks
    into a verifiable artifact suitable for compliance and reporting.

    Attributes:
        tenant_id: Tenant/Institution owning the pipeline run.
        run_id: Unique pipeline execution run identifier.
        status: Overall reconciliation status (`ReconciliationStatus`).
        total_records_processed: Initial total records ingested/read.
        total_records_successful: Final total records successfully completed.
        total_records_rejected: Total distinct records rejected across all stages.
        stage_metrics: Stage-by-stage quantitative breakdown.
        lineage_summary: Sample/full list of tracked lineage records.
        discrepancies: List of discrepancy reports if accounts do not balance perfectly.
        manifest_id: Unique identifier for this audit manifest (UUID4).
        timestamp: UTC timestamp of manifest generation (ISO format).
    """

    tenant_id: str
    run_id: str
    status: ReconciliationStatus
    total_records_processed: int
    total_records_successful: int
    total_records_rejected: int
    stage_metrics: List[StageMetric] = field(default_factory=list)
    lineage_summary: List[LineageRecord] = field(default_factory=list)
    discrepancies: List[Dict[str, Any]] = field(default_factory=list)
    manifest_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
    )


__all__ = [
    "ReconciliationStatus",
    "StageMetric",
    "LineageRecord",
    "PipelineManifest",
]
