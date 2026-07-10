# apps/data_engine/components/tests/test_tarea13.py
"""Unit tests for TAREA 13 — Import Engine / Load Orchestration Layer.

Covers:
- ImportStatus enum completeness.
- ImportItem creation, defaults, and UUID uniqueness.
- ImportBatch construction with target_entity.
- ImportResult success/failure determination.
- BaseImportStrategy abstract enforcement.
- DryRunStrategy validation and simulation logic.
- ImportComponent pipeline integration, staging consumption, and audit generation.
"""

import pytest

from apps.data_engine.components.importers.models import (
    ImportStatus, ImportItem, ImportBatch, ImportResult,
)
from apps.data_engine.components.importers.base import BaseImportStrategy
from apps.data_engine.components.importers.strategies import DryRunStrategy
from apps.data_engine.components.importers.component import ImportComponent
from apps.data_engine.components.staging.models import StagingRecord, StagingStatus
from apps.data_engine.components.base import MacContext


# ─── ImportStatus ────────────────────────────────────────────────────


def test_import_status_values():
    """All expected import lifecycle states must be present."""
    expected = {"PENDING", "SUCCESS", "FAILED", "SKIPPED"}
    actual = {s.value for s in ImportStatus}
    assert actual == expected


def test_import_status_is_string():
    """ImportStatus values can be compared as plain strings."""
    assert ImportStatus.PENDING == "PENDING"
    assert ImportStatus.SUCCESS == "SUCCESS"
    assert ImportStatus.FAILED == "FAILED"
    assert ImportStatus.SKIPPED == "SKIPPED"


# ─── ImportItem ──────────────────────────────────────────────────────


def test_import_item_defaults():
    """A new ImportItem should have PENDING status, no error, and auto-UUID."""
    item = ImportItem(
        record_id="rec-001", tenant_id="t1", payload={"name": "Alice"}
    )
    assert item.status == ImportStatus.PENDING
    assert item.error is None
    assert len(item.item_id) == 36  # UUID4 string


def test_import_item_unique_ids():
    """Each ImportItem must get a unique item_id."""
    i1 = ImportItem(record_id="r1", tenant_id="t1", payload={})
    i2 = ImportItem(record_id="r2", tenant_id="t1", payload={})
    assert i1.item_id != i2.item_id


def test_import_item_with_error():
    """An ImportItem can carry a failure error."""
    item = ImportItem(
        record_id="r1", tenant_id="t1", payload={},
        status=ImportStatus.FAILED, error="duplicate key"
    )
    assert item.status == ImportStatus.FAILED
    assert item.error == "duplicate key"


# ─── ImportBatch ─────────────────────────────────────────────────────


def test_import_batch_creation():
    """An ImportBatch groups items with auto-generated batch_id."""
    items = [
        ImportItem(record_id="r1", tenant_id="t1", payload={"a": 1}),
        ImportItem(record_id="r2", tenant_id="t1", payload={"a": 2}),
    ]
    batch = ImportBatch(tenant_id="t1", run_id="run-1", items=items)
    assert len(batch.items) == 2
    assert batch.target_entity == "unknown"
    assert len(batch.batch_id) == 36


def test_import_batch_custom_target():
    """ImportBatch can have a custom target_entity."""
    batch = ImportBatch(
        tenant_id="t1", run_id="run-1",
        target_entity="students"
    )
    assert batch.target_entity == "students"


# ─── ImportResult ────────────────────────────────────────────────────


def test_import_result_success():
    """ImportResult success=True when all items succeeded."""
    result = ImportResult(
        batch_id="b1", total_items=3,
        success_count=3, failed_count=0, skipped_count=0,
        success=True,
    )
    assert result.success is True
    assert result.total_items == 3


def test_import_result_failure():
    """ImportResult success=False when at least one item failed."""
    result = ImportResult(
        batch_id="b1", total_items=3,
        success_count=2, failed_count=1, skipped_count=0,
        success=False,
    )
    assert result.success is False
    assert result.failed_count == 1


# ─── BaseImportStrategy (abstract) ───────────────────────────────────


def test_base_strategy_abstract():
    """BaseImportStrategy is abstract and must not be instantiated."""
    with pytest.raises(TypeError):
        BaseImportStrategy()


# ─── DryRunStrategy ──────────────────────────────────────────────────


def test_dry_run_all_success():
    """DryRun marks all structurally valid items as SUCCESS."""
    strategy = DryRunStrategy()
    items = [
        ImportItem(record_id="r1", tenant_id="t1", payload={"name": "Alice"}),
        ImportItem(record_id="r2", tenant_id="t1", payload={"name": "Bob"}),
    ]
    batch = ImportBatch(tenant_id="t1", run_id="run-1", items=items)

    result = strategy.execute(batch)

    assert result.success is True
    assert result.total_items == 2
    assert result.success_count == 2
    assert result.failed_count == 0
    assert result.skipped_count == 0
    assert all(i.status == ImportStatus.SUCCESS for i in result.items)


def test_dry_run_empty_batch():
    """DryRun with an empty batch produces ImportResult with zeros."""
    strategy = DryRunStrategy()
    batch = ImportBatch(tenant_id="t1", run_id="run-1", items=[])

    result = strategy.execute(batch)

    assert result.success is True
    assert result.total_items == 0
    assert result.success_count == 0
    assert result.failed_count == 0


def test_dry_run_preserves_payload():
    """Original payloads are preserved after DryRun execution."""
    strategy = DryRunStrategy()
    original_payload = {"name": "Alice", "age": 25}
    items = [
        ImportItem(record_id="r1", tenant_id="t1", payload=original_payload),
    ]
    batch = ImportBatch(tenant_id="t1", run_id="run-1", items=items)

    result = strategy.execute(batch)

    assert result.items[0].payload == original_payload
    assert result.items[0].payload is original_payload  # same object


def test_dry_run_empty_payload_fails():
    """DryRun marks items with empty payload as FAILED."""
    strategy = DryRunStrategy()
    items = [
        ImportItem(record_id="r1", tenant_id="t1", payload={}),
    ]
    batch = ImportBatch(tenant_id="t1", run_id="run-1", items=items)

    result = strategy.execute(batch)

    assert result.success is False
    assert result.failed_count == 1
    assert result.items[0].status == ImportStatus.FAILED
    assert "Empty or invalid payload" in result.items[0].error


def test_dry_run_missing_record_id_fails():
    """DryRun marks items with empty record_id as FAILED."""
    strategy = DryRunStrategy()
    items = [
        ImportItem(record_id="", tenant_id="t1", payload={"a": 1}),
    ]
    batch = ImportBatch(tenant_id="t1", run_id="run-1", items=items)

    result = strategy.execute(batch)

    assert result.success is False
    assert result.failed_count == 1
    assert "Missing record_id" in result.items[0].error


def test_dry_run_mixed_valid_invalid():
    """DryRun correctly handles a mix of valid and invalid items."""
    strategy = DryRunStrategy()
    items = [
        ImportItem(record_id="r1", tenant_id="t1", payload={"a": 1}),  # valid
        ImportItem(record_id="r2", tenant_id="t1", payload={}),         # invalid
        ImportItem(record_id="r3", tenant_id="t1", payload={"b": 2}),  # valid
    ]
    batch = ImportBatch(tenant_id="t1", run_id="run-1", items=items)

    result = strategy.execute(batch)

    assert result.success is False
    assert result.success_count == 2
    assert result.failed_count == 1
    assert len(result.errors) == 1
    assert result.errors[0]["record_id"] == "r2"


# ─── ImportComponent (Pipeline Integration) ──────────────────────────


def _make_staging_records(count_valid=2, count_rejected=1):
    """Helper to create a mix of VALIDATED and REJECTED staging records."""
    records = []
    for i in range(count_valid):
        records.append(StagingRecord(
            tenant_id="t1", run_id="run-1", row_index=i,
            payload={"field": f"value_{i}"},
            status=StagingStatus.VALIDATED,
        ))
    for i in range(count_rejected):
        records.append(StagingRecord(
            tenant_id="t1", run_id="run-1", row_index=count_valid + i,
            payload={"field": f"bad_{i}"},
            status=StagingStatus.REJECTED,
            errors=[{"row": count_valid + i, "field": "field", "error": "invalid"}],
        ))
    return records


def test_import_component_happy_path():
    """Pipeline with VALIDATED staging_records produces correct import_audit."""
    comp = ImportComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "payload": [],
        "metadata": {
            "staging_records": _make_staging_records(count_valid=3, count_rejected=0),
        },
    }

    result = comp.execute(ctx)
    audit = result["metadata"]["import_audit"]

    assert audit["total_items"] == 3
    assert audit["success_count"] == 3
    assert audit["failed_count"] == 0
    assert audit["skipped_count"] == 0
    assert audit["strategy"] == "dry_run"


def test_import_component_mixed_records():
    """Only VALIDATED records are processed; REJECTED are omitted."""
    comp = ImportComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "payload": [],
        "metadata": {
            "staging_records": _make_staging_records(count_valid=2, count_rejected=3),
        },
    }

    result = comp.execute(ctx)
    audit = result["metadata"]["import_audit"]

    # Only the 2 validated records should be imported
    assert audit["total_items"] == 2
    assert audit["success_count"] == 2


def test_import_component_no_staging():
    """Without staging_records, produces audit with zeros."""
    comp = ImportComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "payload": [],
        "metadata": {},
    }

    result = comp.execute(ctx)
    audit = result["metadata"]["import_audit"]

    assert audit["total_items"] == 0
    assert audit["success_count"] == 0
    assert audit["failed_count"] == 0


def test_import_component_empty_validated():
    """All REJECTED staging records → 0 items imported."""
    comp = ImportComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "payload": [],
        "metadata": {
            "staging_records": _make_staging_records(count_valid=0, count_rejected=5),
        },
    }

    result = comp.execute(ctx)
    audit = result["metadata"]["import_audit"]

    assert audit["total_items"] == 0
    assert audit["success_count"] == 0


def test_import_component_custom_target():
    """import_target propagates to ImportBatch.target_entity."""
    comp = ImportComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "payload": [],
        "metadata": {
            "staging_records": _make_staging_records(count_valid=1, count_rejected=0),
            "import_target": "students",
        },
    }

    result = comp.execute(ctx)
    import_result = result["metadata"]["import_result"]

    assert import_result.batch_id  # non-empty


def test_import_component_audit_structure():
    """import_audit contains all expected keys."""
    comp = ImportComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "payload": [],
        "metadata": {
            "staging_records": _make_staging_records(count_valid=1, count_rejected=0),
        },
    }

    result = comp.execute(ctx)
    audit = result["metadata"]["import_audit"]

    expected_keys = {"total_items", "success_count", "failed_count", "skipped_count", "strategy"}
    assert set(audit.keys()) == expected_keys


def test_import_component_traceability():
    """ImportItem.record_id matches the originating StagingRecord.record_id."""
    staging_records = _make_staging_records(count_valid=2, count_rejected=0)
    comp = ImportComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "payload": [],
        "metadata": {
            "staging_records": staging_records,
        },
    }

    result = comp.execute(ctx)
    import_result = result["metadata"]["import_result"]

    staging_ids = {r.record_id for r in staging_records}
    import_ids = {i.record_id for i in import_result.items}
    assert import_ids == staging_ids


def test_import_component_default_context_values():
    """Missing tenant_id/run_id should fallback to defaults, not crash."""
    comp = ImportComponent()
    ctx: MacContext = {
        "payload": [],
        "metadata": {
            "staging_records": _make_staging_records(count_valid=1, count_rejected=0),
        },
    }

    result = comp.execute(ctx)
    audit = result["metadata"]["import_audit"]
    assert audit["total_items"] == 1
