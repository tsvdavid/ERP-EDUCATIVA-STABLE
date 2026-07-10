# apps/data_engine/components/exporters/base.py
"""Abstract contracts for the MAC Export Engine.

Defines:
- ``BaseOutputFormatter``: Interface for transforming domain batches into target format representations.
- ``BaseOutputDispatcher``: Interface for dispatching formatted outputs to destinations.
- ``BaseExportStrategy``: Unified strategy interface coordinating formatting and dispatching.
- ``BaseExporter``: Abstract pipeline component base for all exporter components.
"""

from abc import ABC, abstractmethod
from typing import Any

from apps.data_engine.components.base import BaseComponent, component_name
from .models import ExportBatch, ExportResult


class BaseOutputFormatter(ABC):
    """Abstract contract for transforming domain batches into target formats."""

    @abstractmethod
    def format(self, batch: ExportBatch) -> Any:
        """Transform batch items into structured output representation.

        Args:
            batch: The ``ExportBatch`` containing items to format.

        Returns:
            Formatted data representation (e.g. dict, string, payload envelope).
        """
        raise NotImplementedError  # pragma: no cover


class BaseOutputDispatcher(ABC):
    """Abstract contract for dispatching formatted outputs to external targets."""

    @abstractmethod
    def dispatch(self, batch: ExportBatch, formatted_data: Any) -> ExportResult:
        """Deliver formatted_data to target destination and produce consolidated result.

        Args:
            batch: The originating ``ExportBatch``.
            formatted_data: Output produced by a ``BaseOutputFormatter``.

        Returns:
            Consolidated ``ExportResult`` with item statuses and output payload.
        """
        raise NotImplementedError  # pragma: no cover


class BaseExportStrategy(ABC):
    """Unified strategy interface coordinating formatting and dispatching.

    Decouples export orchestration from physical I/O and serialization details.
    """

    @abstractmethod
    def execute(self, batch: ExportBatch) -> ExportResult:
        """Process an export batch from validation to simulated/real dispatch.

        Args:
            batch: The ``ExportBatch`` to export.

        Returns:
            Consolidated ``ExportResult``.
        """
        raise NotImplementedError  # pragma: no cover


class BaseExporter(BaseComponent, ABC):
    """Abstract base for all exporter components within MAC.

    Subclasses must implement ``execute(self, context)`` and should expose a
    ``component_type`` attribute with the value ``"exporter"``.
    """

    component_type: str = "exporter"


__all__ = [
    "BaseOutputFormatter",
    "BaseOutputDispatcher",
    "BaseExportStrategy",
    "BaseExporter",
    "component_name",
]
