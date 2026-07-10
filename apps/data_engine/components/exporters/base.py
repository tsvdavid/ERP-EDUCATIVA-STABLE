# apps/data_engine/components/exporters/base.py
"""Base classes for MAC exporters.

Exporters take processed data from the pipeline and persist or export it to
external destinations. They follow the same contract as other MAC components.
"""

from abc import ABC
from .base import BaseComponent, component_name

class BaseExporter(BaseComponent, ABC):
    """Abstract base for all exporter components.

    Sub‑classes must implement ``execute(self, context)`` and should expose a
    ``component_type`` attribute with the value ``"exporter"`` so that the
    orchestrator can log the component type.
    """

    component_type: str = "exporter"

    # No extra abstract methods – ``execute`` is already abstract in
    # ``BaseComponent``.
