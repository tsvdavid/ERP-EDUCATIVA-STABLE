# apps/data_engine/components/tests/test_tarea14.py
"""Unit tests for TAREA 14 — Export Engine & Output Orchestration Layer.

Covers:
- ExportFormat and ExportStatus enum completeness.
- ExportItem defaults, UUID generation, and isolation fields.
- ExportBatch construction and format/destination targeting.
- ExportResult success calculation.
- Abstract contract enforcement (BaseOutputFormatter, BaseOutputDispatcher, BaseExportStrategy).
- DryRunExportStrategy simulation, structural validation, and multi-tenant check.
- ExportComponent hierarchical data consumption (import_result -> staging_records -> payload).
- ExportComponent format resolution, audit metadata injection, and traceability preservation.
"""

import pytest

from apps.data_engine.components.base import MacContext
from apps.data_engine.components.exporters.base import (
    BaseOutputFormatter,
    BaseOutputDispatcher,
    BaseExportStrategy,
)
from apps.data_engine.components.exporters.models import (
    ExportFormat,
    ExportStatus,
    ExportItem,
    ExportBatch,
    ExportResult,
)
from apps.data_engine.components.exporters.strategies import (
    MemoryExportFormatter,
    SimulatedDispatcher,
    DryRunExportStrategy,
)
from apps.data_engine.components.exporters.component import ExportComponent
from apps.data_engine.components.importers.models import ImportResult, ImportItem, ImportStatus
from apps.data_engine.components.staging.models import StagingRecord, StagingStatus


# ─── 14.1 Domain Entities ─────────────────────────────────────────────


def test_export_format_enum_values():
    """Verify all 8 target output formats are defined."""
    expected = {
        "CSV",
        "EXCEL",
        "JSON",
        "API_PAYLOAD",
        "S3_OBJECT",
        "QUEUE_MESSAGE",
        "ERP_SYNC",
        "CUSTOM",
    }
    actual = {f.value for f in ExportFormat}
    assert actual == expected


def test_export_status_enum_values():
    """Verify all 5 export lifecycle states are present."""
    expected = {"PENDING", "FORMATTING", "DISPATCHED", "COMPLETED", "FAILED"}
    actual = {s.value for s in ExportStatus}
    assert actual == expected


def test_export_item_defaults_and_uuids():
    """An ExportItem starts in PENDING state and auto-generates unique item_id."""
    i1 = ExportItem(record_id="rec-1", tenant_id="t1", payload={"a": 1})
    i2 = ExportItem(record_id="rec-2", tenant_id="t1", payload={"a": 2})
    assert i1.status == ExportStatus.PENDING
    assert i1.error is None
    assert len(i1.item_id) == 36
    assert i1.item_id != i2.item_id


def test_export_batch_structure():
    """Verify ExportBatch defaults and initialization."""
    items = [ExportItem(record_id="r1", tenant_id="t1", payload={"x": 1})]
    batch = ExportBatch(
        tenant_id="t1",
        run_id="run-101",
        items=items,
        format=ExportFormat.CSV,
        destination="file://out.csv",
    )
    assert batch.format == ExportFormat.CSV
    assert batch.destination == "file://out.csv"
    assert len(batch.items) == 1
    assert len(batch.batch_id) == 36


def test_export_result_success_determination():
    """Verify success flag reflects whether any items failed."""
    success_res = ExportResult(
        batch_id="b1",
        format=ExportFormat.JSON,
        destination="memory://test",
        total_items=2,
        exported_count=2,
        failed_count=0,
        success=True,
    )
    assert success_res.success is True

    failure_res = ExportResult(
        batch_id="b2",
        format=ExportFormat.JSON,
        destination="memory://test",
        total_items=2,
        exported_count=1,
        failed_count=1,
        success=False,
    )
    assert failure_res.success is False


# ─── 14.2 Abstract Contracts & Strategies ─────────────────────────────


def test_base_contracts_cannot_be_instantiated():
    """Verify abstract classes enforce implementation contract."""
    with pytest.raises(TypeError):
        BaseOutputFormatter()
    with pytest.raises(TypeError):
        BaseOutputDispatcher()
    with pytest.raises(TypeError):
        BaseExportStrategy()


def test_dry_run_strategy_all_success():
    """DryRun strategy validates, formats, and simulates dispatch cleanly."""
    strategy = DryRunExportStrategy()
    items = [
        ExportItem(record_id="r1", tenant_id="t1", payload={"name": "Alice"}),
        ExportItem(record_id="r2", tenant_id="t1", payload={"name": "Bob"}),
    ]
    batch = ExportBatch(tenant_id="t1", run_id="run-1", items=items)

    result = strategy.execute(batch)

    assert result.success is True
    assert result.total_items == 2
    assert result.exported_count == 2
    assert result.failed_count == 0
    assert all(i.status == ExportStatus.COMPLETED for i in result.items)
    assert isinstance(result.output_payload, dict)
    assert result.output_payload["total_formatted"] == 2


def test_dry_run_strategy_empty_batch():
    """Empty batch returns 0 items cleanly."""
    strategy = DryRunExportStrategy()
    batch = ExportBatch(tenant_id="t1", run_id="run-1", items=[])

    result = strategy.execute(batch)

    assert result.success is True
    assert result.total_items == 0
    assert result.exported_count == 0
    assert result.output_payload["total_formatted"] == 0


def test_dry_run_strategy_invalid_item_payload():
    """Items with empty/invalid payload or missing record_id are marked FAILED."""
    strategy = DryRunExportStrategy()
    items = [
        ExportItem(record_id="r1", tenant_id="t1", payload={}),  # empty payload
        ExportItem(record_id="", tenant_id="t1", payload={"a": 1}),  # empty record_id
        ExportItem(record_id="r3", tenant_id="t1", payload={"b": 2}),  # valid
    ]
    batch = ExportBatch(tenant_id="t1", run_id="run-1", items=items)

    result = strategy.execute(batch)

    assert result.success is False
    assert result.total_items == 3
    assert result.exported_count == 1
    assert result.failed_count == 2
    assert len(result.errors) == 2
    assert result.items[0].status == ExportStatus.FAILED
    assert "payload" in result.items[0].error
    assert result.items[1].status == ExportStatus.FAILED
    assert "record_id" in result.items[1].error


def test_dry_run_strategy_tenant_isolation_check():
    """Simulated dispatcher fails items whose tenant_id differs from batch.tenant_id."""
    strategy = DryRunExportStrategy()
    items = [
        ExportItem(record_id="r1", tenant_id="t1", payload={"a": 1}),
        ExportItem(record_id="r2", tenant_id="OTHER_TENANT", payload={"a": 2}),
    ]
    batch = ExportBatch(tenant_id="t1", run_id="run-1", items=items)

    result = strategy.execute(batch)

    assert result.success is False
    assert result.exported_count == 1
    assert result.failed_count == 1
    assert result.items[1].status == ExportStatus.FAILED
    assert "Tenant isolation violation" in result.items[1].error


# ─── 14.3 ExportComponent Adapter ─────────────────────────────────────


def test_export_component_consumes_import_result():
    """Verify Priority 1: only SUCCESS items from import_result are exported."""
    comp = ExportComponent()
    import_items = [
        ImportItem(record_id="r1", tenant_id="t1", payload={"k": 1}, status=ImportStatus.SUCCESS),
        ImportItem(record_id="r2", tenant_id="t1", payload={"k": 2}, status=ImportStatus.FAILED, error="err"),
        ImportItem(record_id="r3", tenant_id="t1", payload={"k": 3}, status=ImportStatus.SUCCESS),
    ]
    import_result = ImportResult(
        batch_id="b-imp", total_items=3, success_count=2, failed_count=1, skipped_count=0,
        success=False, items=import_items
    )
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "metadata": {"import_result": import_result},
    }

    res_ctx = comp.execute(ctx)
    audit = res_ctx["metadata"]["export_audit"]

    assert audit["total_items"] == 2
    assert audit["exported_count"] == 2
    assert audit["failed_count"] == 0


def test_export_component_consumes_staging_records():
    """Verify Priority 2: when no import_result, consumes VALIDATED staging_records."""
    comp = ExportComponent()
    staging_records = [
        StagingRecord(tenant_id="t1", run_id="run-1", row_index=1, payload={"a": "1"}, status=StagingStatus.VALIDATED),
        StagingRecord(tenant_id="t1", run_id="run-1", row_index=2, payload={"a": "bad"}, status=StagingStatus.REJECTED),
    ]
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "metadata": {"staging_records": staging_records},
    }

    res_ctx = comp.execute(ctx)
    audit = res_ctx["metadata"]["export_audit"]

    assert audit["total_items"] == 1
    assert audit["exported_count"] == 1


def test_export_component_consumes_raw_payload():
    """Verify Priority 3: when neither staging nor import exist, consumes payload dictionary rows."""
    comp = ExportComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "payload": {"records": [{"id": "usr-1", "name": "Ana"}, {"id": "usr-2", "name": "Luis"}]},
        "metadata": {},
    }

    res_ctx = comp.execute(ctx)
    audit = res_ctx["metadata"]["export_audit"]

    assert audit["total_items"] == 2
    assert audit["exported_count"] == 2
    res_obj = res_ctx["metadata"]["export_result"]
    assert res_obj.items[0].record_id == "usr-1"
    assert res_obj.items[1].record_id == "usr-2"


def test_export_component_audit_injection():
    """Verify exact keys injected into context['metadata']['export_audit']."""
    comp = ExportComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "payload": [{"x": 10}],
        "metadata": {},
    }

    res_ctx = comp.execute(ctx)
    audit = res_ctx["metadata"]["export_audit"]

    expected_keys = {"total_items", "exported_count", "failed_count", "format", "destination", "strategy"}
    assert set(audit.keys()) == expected_keys
    assert audit["format"] == "JSON"
    assert audit["destination"] == "memory://default"
    assert audit["strategy"] == "dry_run"


def test_export_component_traceability_chain():
    """Verify record_id flows intact from StagingRecord to ExportItem."""
    comp = ExportComponent()
    rec = StagingRecord(
        tenant_id="t1", run_id="run-1", row_index=5,
        payload={"score": 95}, status=StagingStatus.VALIDATED
    )
    # StagingRecord auto-generates a UUID record_id
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "metadata": {"staging_records": [rec]},
    }

    res_ctx = comp.execute(ctx)
    export_result = res_ctx["metadata"]["export_result"]

    assert len(export_result.items) == 1
    assert export_result.items[0].record_id == rec.record_id


def test_export_component_custom_config():
    """Verify custom target format and destination resolved from export_config."""
    comp = ExportComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "run-1",
        "payload": [{"data": "hello"}],
        "metadata": {
            "export_config": {
                "format": "csv",
                "destination": "s3://eduka360-exports/results.csv",
            }
        },
    }

    res_ctx = comp.execute(ctx)
    audit = res_ctx["metadata"]["export_audit"]
    res_obj = res_ctx["metadata"]["export_result"]

    assert audit["format"] == "CSV"
    assert audit["destination"] == "s3://eduka360-exports/results.csv"
    assert res_obj.format == ExportFormat.CSV


def test_resolve_format_edge_cases():
    """Verify safe fallback for unknown string formats."""
    comp = ExportComponent()
    assert comp._resolve_format("EXCEL") == ExportFormat.EXCEL
    assert comp._resolve_format(ExportFormat.S3_OBJECT) == ExportFormat.S3_OBJECT
    assert comp._resolve_format("unknown_format") == ExportFormat.CUSTOM
