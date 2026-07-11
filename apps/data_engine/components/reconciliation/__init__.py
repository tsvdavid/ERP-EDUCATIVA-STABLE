# apps/data_engine/components/reconciliation/__init__.py
"""Reconciliation, Lineage & Audit Engine for the MAC subsystem (TAREA 15).

Provides centralized, decoupled pipeline monitoring, quantitative stage balance checks,
record lineage reconstruction, and immutable manifest generation without coupling to any ORM.
"""

from .models import (
    ReconciliationStatus,
    StageMetric,
    LineageRecord,
    PipelineManifest,
)
from .base import (
    BaseLineageTracker,
    BaseReconciliationStrategy,
    BaseAuditExporter,
    BaseReconciler,
)
from .strategies import (
    StandardLineageTracker,
    StrictReconciliationStrategy,
    MemoryAuditExporter,
)
from .component import ReconciliationComponent

__all__ = [
    # Models
    "ReconciliationStatus",
    "StageMetric",
    "LineageRecord",
    "PipelineManifest",
    # Contracts
    "BaseLineageTracker",
    "BaseReconciliationStrategy",
    "BaseAuditExporter",
    "BaseReconciler",
    # Strategies
    "StandardLineageTracker",
    "StrictReconciliationStrategy",
    "MemoryAuditExporter",
    # Component
    "ReconciliationComponent",
]
