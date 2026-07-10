# apps/data_engine/components/exporters/strategies.py
"""Concrete export formatters, dispatchers, and strategies for MAC.

Defines:
- ``MemoryExportFormatter``: Formats batch records into a structured in-memory representation.
- ``SimulatedDispatcher``: Simulates dispatching to external targets without physical I/O, enforcing tenant isolation.
- ``DryRunExportStrategy``: Unified simulation strategy coordinating validation, formatting, and dispatching.
"""

from typing import Any, Dict, List, Optional

from .base import BaseOutputFormatter, BaseOutputDispatcher, BaseExportStrategy
from .models import ExportBatch, ExportItem, ExportResult, ExportStatus


class MemoryExportFormatter(BaseOutputFormatter):
    """Formats export items into a structured dictionary representation.

    Can be consumed by downstream simulation tasks or API responses.
    """

    def format(self, batch: ExportBatch) -> Dict[str, Any]:
        """Structure batch records into a canonical output payload.

        Args:
            batch: The ``ExportBatch`` to format.

        Returns:
            Dictionary containing metadata, format info, and record list.
        """
        output_records = []
        for item in batch.items:
            # Only include items that haven't failed pre-validation
            if item.status != ExportStatus.FAILED:
                output_records.append({
                    "item_id": item.item_id,
                    "record_id": item.record_id,
                    "tenant_id": item.tenant_id,
                    "payload": item.payload,
                })

        format_str = (
            batch.format.value
            if hasattr(batch.format, "value")
            else str(batch.format)
        )

        return {
            "format": format_str,
            "destination": batch.destination,
            "total_formatted": len(output_records),
            "records": output_records,
            "metadata": batch.metadata,
        }


class SimulatedDispatcher(BaseOutputDispatcher):
    """Simulates dispatching formatted outputs without performing physical I/O.

    Enforces multi-tenant isolation across all batch items.
    """

    def dispatch(
        self, batch: ExportBatch, formatted_data: Any
    ) -> ExportResult:
        """Simulate dispatching and update item statuses.

        Args:
            batch: The originating batch.
            formatted_data: The output produced by the formatter.

        Returns:
            Consolidated ``ExportResult``.
        """
        errors: List[Dict[str, Any]] = []

        for item in batch.items:
            # If already failed during validation, record and skip
            if item.status == ExportStatus.FAILED:
                errors.append({
                    "item_id": item.item_id,
                    "record_id": item.record_id,
                    "error": item.error or "Validation failed",
                })
                continue

            # Check tenant isolation
            if item.tenant_id != batch.tenant_id:
                item.status = ExportStatus.FAILED
                item.error = (
                    f"Tenant isolation violation: item tenant ({item.tenant_id}) "
                    f"does not match batch tenant ({batch.tenant_id})"
                )
                errors.append({
                    "item_id": item.item_id,
                    "record_id": item.record_id,
                    "error": item.error,
                })
            else:
                item.status = ExportStatus.COMPLETED

        exported_count = sum(
            1 for i in batch.items if i.status == ExportStatus.COMPLETED
        )
        failed_count = sum(
            1 for i in batch.items if i.status == ExportStatus.FAILED
        )

        return ExportResult(
            batch_id=batch.batch_id,
            format=batch.format,
            destination=batch.destination,
            total_items=len(batch.items),
            exported_count=exported_count,
            failed_count=failed_count,
            success=(failed_count == 0),
            items=batch.items,
            output_payload=formatted_data,
            errors=errors,
        )


class DryRunExportStrategy(BaseExportStrategy):
    """Simulation strategy that validates and formats without external I/O.

    Performs structural checks on items:
    - Non-empty dictionary payload.
    - Non-empty record_id.

    Valid items transition to COMPLETED via simulated dispatch.
    Invalid items transition to FAILED with detailed error tracking.
    """

    strategy_name: str = "dry_run"

    def __init__(
        self,
        formatter: Optional[BaseOutputFormatter] = None,
        dispatcher: Optional[BaseOutputDispatcher] = None,
    ):
        self._formatter = formatter or MemoryExportFormatter()
        self._dispatcher = dispatcher or SimulatedDispatcher()

    def execute(self, batch: ExportBatch) -> ExportResult:
        """Execute validation, formatting, and dispatch simulation.

        Args:
            batch: The batch to process.

        Returns:
            Consolidated ``ExportResult``.
        """
        # Pre-validate items before formatting
        for item in batch.items:
            validation_error = self._validate_item(item)
            if validation_error:
                item.status = ExportStatus.FAILED
                item.error = validation_error
            elif item.status == ExportStatus.PENDING:
                item.status = ExportStatus.FORMATTING

        # Format output payload
        formatted_data = self._formatter.format(batch)

        # Dispatch formatted payload
        return self._dispatcher.dispatch(batch, formatted_data)

    @staticmethod
    def _validate_item(item: ExportItem) -> Optional[str]:
        """Return error message if item structure is invalid."""
        if not item.record_id:
            return "Missing record_id: cannot trace back to source"
        if not isinstance(item.payload, dict) or not item.payload:
            return "Empty or invalid payload: nothing to export"
        return None


__all__ = [
    "MemoryExportFormatter",
    "SimulatedDispatcher",
    "DryRunExportStrategy",
]
