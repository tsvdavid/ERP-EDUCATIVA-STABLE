# apps/data_engine/components/reconciliation/base.py
"""Abstract contracts for the MAC Reconciliation, Lineage & Audit Engine.

Defines:
- ``BaseLineageTracker``: Interface for inspecting pipeline context and reconstructing record lineage.
- ``BaseReconciliationStrategy``: Interface for verifying quantitative balance and multi-tenant integrity.
- ``BaseAuditExporter``: Interface for publishing or attaching the final ``PipelineManifest``.
- ``BaseReconciler``: Abstract pipeline component base for all reconciliation components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from apps.data_engine.components.base import BaseComponent, component_name
from .models import LineageRecord, PipelineManifest


class BaseLineageTracker(ABC):
    """Abstract contract for reconstructing data lineage across pipeline stages."""

    @abstractmethod
    def track(self, context: Dict[str, Any]) -> List[LineageRecord]:
        """Inspect context metadata and build end-to-end lineage records.

        Args:
            context: The pipeline execution context (`MacContext`).

        Returns:
            List of ``LineageRecord`` objects representing tracked items.
        """
        raise NotImplementedError  # pragma: no cover


class BaseReconciliationStrategy(ABC):
    """Abstract contract for auditing quantitative balance and integrity."""

    @abstractmethod
    def reconcile(
        self, context: Dict[str, Any], lineage: List[LineageRecord]
    ) -> PipelineManifest:
        """Audit stage metrics, check multi-tenancy, and produce immutable manifest.

        Args:
            context: The pipeline execution context (`MacContext`).
            lineage: The list of lineage records tracked by a `BaseLineageTracker`.

        Returns:
            Consolidated ``PipelineManifest``.
        """
        raise NotImplementedError  # pragma: no cover


class BaseAuditExporter(ABC):
    """Abstract contract for exporting or attaching the `PipelineManifest`."""

    @abstractmethod
    def export(
        self, context: Dict[str, Any], manifest: PipelineManifest
    ) -> Dict[str, Any]:
        """Serialize or publish the audit manifest and return audit summary.

        Args:
            context: The pipeline execution context (`MacContext`).
            manifest: The `PipelineManifest` produced during reconciliation.

        Returns:
            Dictionary containing audit execution summary metrics.
        """
        raise NotImplementedError  # pragma: no cover


class BaseReconciler(BaseComponent, ABC):
    """Abstract base for all reconciliation components within MAC.

    Subclasses must implement ``execute(self, context)`` and should expose a
    ``component_type`` attribute with the value ``"reconciler"``.
    """

    component_type: str = "reconciler"


__all__ = [
    "BaseLineageTracker",
    "BaseReconciliationStrategy",
    "BaseAuditExporter",
    "BaseReconciler",
    "component_name",
]
