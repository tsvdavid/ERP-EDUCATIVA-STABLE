# apps/data_engine/components/importers/strategies.py
"""Concrete import strategies for the MAC Import Engine.

``DryRunStrategy`` validates the structural integrity of each import item
without performing any actual persistence. It transitions all valid items
from PENDING to SUCCESS and marks structurally invalid items as FAILED.
"""

from typing import Any, Dict, List

from .base import BaseImportStrategy
from .models import ImportBatch, ImportItem, ImportResult, ImportStatus


class DryRunStrategy(BaseImportStrategy):
    """Simulation strategy that validates structure without persisting.

    Validation rules (minimal structural checks):
    - The item's payload must be a non-empty dict.
    - The item must have a non-empty record_id.

    Items passing validation are marked SUCCESS.
    Items failing are marked FAILED with an error message.
    """

    strategy_name: str = "dry_run"

    def execute(self, batch: ImportBatch) -> ImportResult:
        """Simulate import by validating item structure.

        Args:
            batch: The batch to process.

        Returns:
            ImportResult with all items transitioned to SUCCESS or FAILED.
        """
        errors: List[Dict[str, Any]] = []

        for item in batch.items:
            validation_error = self._validate_item(item)
            if validation_error:
                item.status = ImportStatus.FAILED
                item.error = validation_error
                errors.append({
                    "item_id": item.item_id,
                    "record_id": item.record_id,
                    "error": validation_error,
                })
            else:
                item.status = ImportStatus.SUCCESS

        success_count = sum(
            1 for i in batch.items if i.status == ImportStatus.SUCCESS
        )
        failed_count = sum(
            1 for i in batch.items if i.status == ImportStatus.FAILED
        )
        skipped_count = sum(
            1 for i in batch.items if i.status == ImportStatus.SKIPPED
        )

        return ImportResult(
            batch_id=batch.batch_id,
            total_items=len(batch.items),
            success_count=success_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            success=(failed_count == 0),
            items=batch.items,
            errors=errors,
        )

    @staticmethod
    def _validate_item(item: ImportItem) -> str | None:
        """Return an error message if the item is structurally invalid."""
        if not item.record_id:
            return "Missing record_id: cannot trace back to staging"
        if not isinstance(item.payload, dict) or not item.payload:
            return "Empty or invalid payload: nothing to import"
        return None


__all__ = ["DryRunStrategy"]
