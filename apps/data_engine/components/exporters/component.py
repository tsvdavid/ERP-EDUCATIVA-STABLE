# apps/data_engine/components/exporters/component.py
"""ExportComponent — MAC pipeline adapter for the Export Engine.

Sits at the end of the pipeline and:
1. Reads configuration from ``context.metadata.export_config``.
2. Extracts data hierarchically with deterministic priority:
   - Priority 1: ``import_result`` (SUCCESS items from TAREA 13).
   - Priority 2: ``staging_records`` (VALIDATED records from TAREA 12).
   - Priority 3: ``payload`` raw or transformed dictionary rows.
3. Builds an ``ExportBatch`` with target format and destination.
4. Delegates to the injected ``BaseExportStrategy`` (default: DryRunExportStrategy).
5. Injects ``export_audit`` and ``export_result`` into context metadata.
"""

from typing import Any, Dict, List, Optional

from apps.data_engine.components.base import MacContext
from apps.data_engine.components.importers.models import ImportResult, ImportStatus
from apps.data_engine.components.staging.models import StagingRecord, StagingStatus

from .base import BaseExporter, BaseExportStrategy
from .models import ExportBatch, ExportFormat, ExportItem
from .strategies import DryRunExportStrategy


class ExportComponent(BaseExporter):
    """Pipeline adapter that bridges the MAC data flow with the Export Engine.

    If no strategy is injected, a ``DryRunExportStrategy`` is used by default,
    ensuring the component is self-contained for testing and simulation.
    """

    component_type = "exporter"

    def __init__(self, strategy: Optional[BaseExportStrategy] = None):
        self._strategy = strategy or DryRunExportStrategy()

    def execute(self, context: MacContext) -> MacContext:
        """Process the context and execute export orchestration.

        Args:
            context: The pipeline execution context.

        Returns:
            The context enriched with ``metadata.export_audit`` and ``metadata.export_result``.
        """
        tenant_id = context.get("tenant_id", "default")
        run_id = context.get("run_id", "unknown")
        metadata = context.get("metadata", {})
        export_config = metadata.get("export_config", {})

        # Resolve target format and destination
        format_val = export_config.get("format", "JSON")
        format_enum = self._resolve_format(format_val)
        destination = export_config.get("destination", "memory://default")
        extra_metadata = export_config.get("metadata", {})

        # Hierarchical data extraction
        items = self._extract_items(context, tenant_id, metadata)

        # Build export batch
        batch = ExportBatch(
            tenant_id=tenant_id,
            run_id=run_id,
            items=items,
            format=format_enum,
            destination=destination,
            metadata=extra_metadata,
        )

        # Execute export strategy
        result = self._strategy.execute(batch)

        # Determine strategy name for audit
        strategy_name = getattr(
            self._strategy, "strategy_name", type(self._strategy).__name__
        )

        # Inject audit and result into context metadata
        if "metadata" not in context:
            context["metadata"] = {}

        format_str = (
            result.format.value
            if hasattr(result.format, "value")
            else str(result.format)
        )

        context["metadata"]["export_audit"] = {
            "total_items": result.total_items,
            "exported_count": result.exported_count,
            "failed_count": result.failed_count,
            "format": format_str,
            "destination": result.destination,
            "strategy": strategy_name,
        }
        context["metadata"]["export_result"] = result

        return context

    @staticmethod
    def _resolve_format(format_val: Any) -> ExportFormat:
        """Safely resolve an input format string/enum to an ExportFormat enum."""
        if isinstance(format_val, ExportFormat):
            return format_val
        if isinstance(format_val, str):
            clean_str = format_val.strip().upper()
            try:
                return ExportFormat[clean_str]
            except KeyError:
                try:
                    return ExportFormat(clean_str)
                except ValueError:
                    return ExportFormat.CUSTOM
        return ExportFormat.CUSTOM

    @staticmethod
    def _extract_items(
        context: MacContext, tenant_id: str, metadata: Dict[str, Any]
    ) -> List[ExportItem]:
        """Extract domain items hierarchically from context."""
        # Priority 1: import_result
        if "import_result" in metadata:
            import_res = metadata["import_result"]
            if isinstance(import_res, ImportResult):
                return [
                    ExportItem(
                        record_id=item.record_id,
                        tenant_id=item.tenant_id,
                        payload=item.payload,
                    )
                    for item in import_res.items
                    if item.status == ImportStatus.SUCCESS
                ]

        # Priority 2: staging_records
        if "staging_records" in metadata:
            staging_recs = metadata.get("staging_records", [])
            return [
                ExportItem(
                    record_id=rec.record_id,
                    tenant_id=rec.tenant_id,
                    payload=rec.payload,
                )
                for rec in staging_recs
                if isinstance(rec, StagingRecord) and rec.status == StagingStatus.VALIDATED
            ]

        # Priority 3: raw / transformed payload fallback
        payload = context.get("payload", [])
        if isinstance(payload, dict):
            records = payload.get("records", [])
        elif isinstance(payload, list):
            records = payload
        else:
            records = []

        items = []
        for idx, row in enumerate(records):
            if isinstance(row, dict):
                rec_id = str(row.get("id") or row.get("record_id") or f"payload-row-{idx}")
                items.append(
                    ExportItem(
                        record_id=rec_id,
                        tenant_id=tenant_id,
                        payload=row,
                    )
                )
        return items


__all__ = ["ExportComponent"]
