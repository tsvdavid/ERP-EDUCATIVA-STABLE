# apps/data_engine/components/staging/component.py
"""StagingComponent — MAC pipeline adapter for the Staging Engine.

This component sits after the SchemaValidator in the pipeline.  It:
1. Reads the validated payload and any ``validation_errors`` from the context.
2. Classifies each row as VALIDATED or REJECTED based on whether it has errors.
3. Wraps every row into a ``StagingRecord``.
4. Persists the batch through the injected ``BaseStagingRepository``.
5. Writes a ``staging_audit`` summary back into ``context["metadata"]``.
"""

from typing import Any, Dict, List, Optional

from apps.data_engine.components.base import BaseComponent, MacContext
from .base import BaseStagingRepository
from .models import StagingRecord, StagingStatus
from .repository import MemoryStagingRepository


class StagingComponent(BaseComponent):
    """Pipeline adapter that bridges the MAC data flow with the staging store.

    If no repository is injected, a local ``MemoryStagingRepository`` is
    created per execution to keep the component self-contained.
    """

    component_type = "staging"

    def __init__(self, repository: Optional[BaseStagingRepository] = None):
        self._repository = repository

    def execute(self, context: MacContext) -> MacContext:
        """Process the context and stage records.

        Expected context keys:
        - ``tenant_id``: str
        - ``run_id``: str
        - ``payload``: list of dicts (rows)
        - ``metadata.validation_errors``: list of error dicts (optional)

        Injects into context:
        - ``metadata.staging_audit``: dict with total, validated, rejected counts.
        - ``metadata.staging_records``: list of StagingRecord instances.
        """
        tenant_id = context.get("tenant_id", "default")
        run_id = context.get("run_id", "unknown")
        payload = context.get("payload", [])
        metadata = context.get("metadata", {})
        validation_errors = metadata.get("validation_errors", [])

        # Use the injected repo or create an ephemeral one
        repository = self._repository or MemoryStagingRepository()

        # Index validation errors by row number for O(1) lookup
        errors_by_row: Dict[int, List[Dict[str, Any]]] = {}
        for error in validation_errors:
            row_idx = error.get("row", -1)
            errors_by_row.setdefault(row_idx, []).append(error)

        # Build staging records
        records: List[StagingRecord] = []
        for index, row in enumerate(payload):
            row_errors = errors_by_row.get(index, [])
            status = (
                StagingStatus.REJECTED if row_errors else StagingStatus.VALIDATED
            )
            record = StagingRecord(
                tenant_id=tenant_id,
                run_id=run_id,
                row_index=index,
                payload=row if isinstance(row, dict) else {},
                status=status,
                errors=row_errors,
            )
            records.append(record)

        # Persist the batch
        repository.save_batch(tenant_id, run_id, records)

        # Build audit summary
        validated_count = sum(
            1 for r in records if r.status == StagingStatus.VALIDATED
        )
        rejected_count = sum(
            1 for r in records if r.status == StagingStatus.REJECTED
        )

        # Inject audit into context metadata
        if "metadata" not in context:
            context["metadata"] = {}
        context["metadata"]["staging_audit"] = {
            "total_records": len(records),
            "validated_count": validated_count,
            "rejected_count": rejected_count,
        }
        # Attach records for downstream components or reporting
        context["metadata"]["staging_records"] = records

        return context


__all__ = ["StagingComponent"]
