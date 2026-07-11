# apps/data_engine/components/reconciliation/component.py
"""Pipeline component adapter for the MAC Reconciliation, Lineage & Audit Engine.

Defines `ReconciliationComponent`, which sits at the end of the MAC pipeline,
inspects all metadata audit trails and domain records from layers 1 through 8,
tracks record lineage, verifies quantitative conservation laws, and publishes an
immutable `PipelineManifest` inside `context["metadata"]`.
"""

from typing import Any, Dict, Optional

from .base import (
    BaseAuditExporter,
    BaseLineageTracker,
    BaseReconciler,
    BaseReconciliationStrategy,
)
from .strategies import (
    MemoryAuditExporter,
    StandardLineageTracker,
    StrictReconciliationStrategy,
)


class ReconciliationComponent(BaseReconciler):
    """Orchestrates pipeline reconciliation, lineage tracking, and audit export.

    Acts as the final supervisory component in the MAC pipeline chain:
    Reader -> Parser -> Mapper -> Caster -> SchemaValidator -> Staging -> Import -> Export -> Reconciler

    Parameters:
        tracker: Strategy for tracking data lineage across stages (`BaseLineageTracker`).
        reconciliation_strategy: Strategy for auditing quantitative balance (`BaseReconciliationStrategy`).
        exporter: Strategy for publishing the immutable manifest (`BaseAuditExporter`).
    """

    def __init__(
        self,
        tracker: Optional[BaseLineageTracker] = None,
        reconciliation_strategy: Optional[BaseReconciliationStrategy] = None,
        exporter: Optional[BaseAuditExporter] = None,
    ):
        self._tracker = tracker or StandardLineageTracker()
        self._reconciliation_strategy = (
            reconciliation_strategy or StrictReconciliationStrategy()
        )
        self._exporter = exporter or MemoryAuditExporter()

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect context metadata, verify conservation laws, and attach audit manifest.

        Args:
            context: The pipeline execution dictionary (`MacContext`).

        Returns:
            The mutated context dictionary containing `metadata["reconciliation_audit"]`
            and `metadata["pipeline_manifest"]`.
        """
        if not isinstance(context, dict):
            raise TypeError(
                f"ReconciliationComponent expects context of type dict, got {type(context).__name__}"
            )

        if "metadata" not in context or not isinstance(context["metadata"], dict):
            context["metadata"] = {}

        # 1. Reconstruct record lineage from context metadata across all prior stages
        lineage = self._tracker.track(context)

        # 2. Audit stage-by-stage quantitative metrics and check multi-tenant isolation
        manifest = self._reconciliation_strategy.reconcile(context, lineage)

        # 3. Export/attach immutable manifest to context metadata
        audit_summary = self._exporter.export(context, manifest)

        # 4. Attach summary dict for downstream monitoring and quick inspection
        context["metadata"]["reconciliation_audit"] = audit_summary

        return context


__all__ = ["ReconciliationComponent"]
