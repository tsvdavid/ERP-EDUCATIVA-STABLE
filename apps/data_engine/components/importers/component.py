# apps/data_engine/components/importers/component.py
"""ImportComponent — MAC pipeline adapter for the Import Engine.

This component sits after the StagingComponent in the pipeline. It:
1. Reads ``staging_records`` from the context metadata.
2. Filters only records with status VALIDATED.
3. Transforms each validated StagingRecord into an ImportItem.
4. Groups them into an ImportBatch.
5. Delegates to the injected BaseImportStrategy (default: DryRunStrategy).
6. Writes ``import_audit`` and ``import_result`` back into context metadata.
"""

from typing import Optional

from apps.data_engine.components.base import BaseComponent, MacContext
from apps.data_engine.components.staging.models import StagingRecord, StagingStatus

from .base import BaseImportStrategy
from .models import ImportBatch, ImportItem, ImportStatus
from .strategies import DryRunStrategy


class ImportComponent(BaseComponent):
    """Pipeline adapter that bridges the MAC data flow with the import engine.

    If no strategy is injected, a ``DryRunStrategy`` is used by default,
    ensuring the component is self-contained for testing and simulation.
    """

    component_type = "importer"

    def __init__(self, strategy: Optional[BaseImportStrategy] = None):
        self._strategy = strategy or DryRunStrategy()

    def execute(self, context: MacContext) -> MacContext:
        """Process the context and execute import.

        Expected context keys (from StagingComponent):
        - ``metadata.staging_records``: list of StagingRecord instances.
        - ``metadata.import_target``: str (optional, default: "unknown").

        Injects into context:
        - ``metadata.import_audit``: dict with counts and strategy name.
        - ``metadata.import_result``: ImportResult instance.
        """
        tenant_id = context.get("tenant_id", "default")
        run_id = context.get("run_id", "unknown")
        metadata = context.get("metadata", {})
        staging_records = metadata.get("staging_records", [])
        target_entity = metadata.get("import_target", "unknown")

        # Filter only VALIDATED records from staging
        validated_records = [
            r for r in staging_records
            if isinstance(r, StagingRecord) and r.status == StagingStatus.VALIDATED
        ]

        # Transform StagingRecords into ImportItems
        items = [
            ImportItem(
                record_id=record.record_id,
                tenant_id=record.tenant_id,
                payload=record.payload,
            )
            for record in validated_records
        ]

        # Build the import batch
        batch = ImportBatch(
            tenant_id=tenant_id,
            run_id=run_id,
            items=items,
            target_entity=target_entity,
        )

        # Delegate to strategy
        result = self._strategy.execute(batch)

        # Determine strategy name for audit
        strategy_name = getattr(
            self._strategy, "strategy_name", type(self._strategy).__name__
        )

        # Inject audit into context metadata
        if "metadata" not in context:
            context["metadata"] = {}
        context["metadata"]["import_audit"] = {
            "total_items": result.total_items,
            "success_count": result.success_count,
            "failed_count": result.failed_count,
            "skipped_count": result.skipped_count,
            "strategy": strategy_name,
        }
        context["metadata"]["import_result"] = result

        return context


__all__ = ["ImportComponent"]
