# apps/data_engine/components/tests/test_tarea15.py
"""Unit tests for TAREA 15: MAC Reconciliation, Lineage & Audit Engine.

Verifies:
- Domain models (`ReconciliationStatus`, `StageMetric`, `LineageRecord`, `PipelineManifest`)
- Abstract contracts and enforcement of TypeError on instantiation
- `StandardLineageTracker` across full and partial pipelines + capping behavior
- `StrictReconciliationStrategy` (`BALANCED`, `DISCREPANCY_DETECTED`, `CRITICAL_DROP`, tenant violations)
- `MemoryAuditExporter` output summary and context attachment
- `ReconciliationComponent` adapter execution and type checking
- Integration with `ProcessingResult.from_context`
- Auto-registration via `discovery.py` (`"reconciliation_component"`)
"""

import pytest
from typing import Any, Dict, List

from apps.data_engine.components.reconciliation.models import (
    ReconciliationStatus,
    StageMetric,
    LineageRecord,
    PipelineManifest,
)
from apps.data_engine.components.reconciliation.base import (
    BaseLineageTracker,
    BaseReconciliationStrategy,
    BaseAuditExporter,
    BaseReconciler,
)
from apps.data_engine.components.reconciliation.strategies import (
    StandardLineageTracker,
    StrictReconciliationStrategy,
    MemoryAuditExporter,
)
from apps.data_engine.components.reconciliation.component import ReconciliationComponent
from apps.data_engine.components.staging.models import StagingRecord, StagingStatus
from apps.data_engine.components.importers.models import (
    ImportItem,
    ImportResult,
    ImportStatus,
)
from apps.data_engine.components.exporters.models import (
    ExportFormat,
    ExportItem,
    ExportResult,
    ExportStatus,
)
from apps.data_engine.components.results.processing_result import ProcessingResult
from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.components.discovery import auto_register


class TestReconciliationModels:
    def test_reconciliation_status_enum(self):
        assert ReconciliationStatus.BALANCED.value == "BALANCED"
        assert ReconciliationStatus.DISCREPANCY_DETECTED.value == "DISCREPANCY_DETECTED"
        assert ReconciliationStatus.CRITICAL_DROP.value == "CRITICAL_DROP"
        assert ReconciliationStatus.UNPROCESSED.value == "UNPROCESSED"

    def test_stage_metric_defaults(self):
        sm = StageMetric(
            stage_name="mapping",
            items_in=100,
            items_out=95,
            items_rejected=5,
        )
        assert sm.conversion_rate_pct == 95.0

        sm_zero = StageMetric(
            stage_name="mapping", items_in=0, items_out=0, items_rejected=0
        )
        assert sm_zero.conversion_rate_pct == 0.0

    def test_lineage_record_history(self):
        lr = LineageRecord(
            record_id="rec-001",
            tenant_id="tenant-123",
            stage_history=["staging", "import"],
            final_status="SUCCESS",
            accumulated_errors=["some error"],
        )
        assert lr.record_id == "rec-001"
        assert lr.tenant_id == "tenant-123"
        assert len(lr.stage_history) == 2
        assert "some error" in lr.accumulated_errors

    def test_pipeline_manifest_uuids(self):
        pm = PipelineManifest(
            tenant_id="tenant-abc",
            run_id="run-001",
            status=ReconciliationStatus.BALANCED,
            total_records_processed=10,
            total_records_successful=10,
            total_records_rejected=0,
        )
        assert pm.manifest_id
        assert pm.timestamp
        assert pm.status == ReconciliationStatus.BALANCED


class TestReconciliationContracts:
    def test_base_reconciliation_contracts(self):
        with pytest.raises(TypeError):
            BaseLineageTracker()  # type: ignore

        with pytest.raises(TypeError):
            BaseReconciliationStrategy()  # type: ignore

        with pytest.raises(TypeError):
            BaseAuditExporter()  # type: ignore

        with pytest.raises(TypeError):
            BaseReconciler()  # type: ignore


class TestReconciliationStrategies:
    def test_standard_lineage_tracker_full_pipeline(self):
        tracker = StandardLineageTracker()
        context = {
            "tenant_id": "org-edu",
            "payload": {
                "records": [
                    {"id": "row-1", "name": "Alice"},
                    {"id": "row-2", "name": "Bob"},
                ]
            },
            "metadata": {
                "staging_records": [
                    StagingRecord(
                        record_id="row-1",
                        tenant_id="org-edu",
                        payload={"name": "Alice"},
                        status=StagingStatus.VALIDATED,
                        run_id="run-1",
                        row_index=0,
                    ),
                    StagingRecord(
                        record_id="row-2",
                        tenant_id="org-edu",
                        payload={"name": "Bob"},
                        status=StagingStatus.REJECTED,
                        errors=[{"message": "Invalid format"}],
                        run_id="run-1",
                        row_index=1,
                    ),
                ],
                "import_result": ImportResult(
                    batch_id="batch-1",
                    total_items=1,
                    success_count=1,
                    failed_count=0,
                    skipped_count=0,
                    items=[
                        ImportItem(
                            item_id="it-1",
                            record_id="row-1",
                            tenant_id="org-edu",
                            status=ImportStatus.SUCCESS,
                            payload={"name": "Alice"},
                        )
                    ],
                ),
                "export_result": ExportResult(
                    batch_id="exp-1",
                    format=ExportFormat.JSON,
                    destination="S3",
                    total_items=1,
                    exported_count=1,
                    failed_count=0,
                    items=[
                        ExportItem(
                            item_id="ex-1",
                            record_id="row-1",
                            tenant_id="org-edu",
                            payload={"name": "Alice"},
                            status=ExportStatus.COMPLETED,
                        )
                    ],
                ),
            },
        }

        lineage = tracker.track(context)
        assert len(lineage) == 2
        rec_map = {r.record_id: r for r in lineage}

        assert "row-1" in rec_map
        assert "row-2" in rec_map
        assert rec_map["row-1"].final_status == "COMPLETED"
        assert "export" in rec_map["row-1"].stage_history
        assert rec_map["row-2"].final_status == "REJECTED"
        assert len(rec_map["row-2"].accumulated_errors) == 1

    def test_standard_lineage_tracker_summary_cap(self):
        tracker = StandardLineageTracker(max_records_summary=3)
        context = {
            "tenant_id": "org-edu",
            "payload": [
                {"id": f"row-{i}", "data": f"val-{i}"} for i in range(10)
            ],
            "metadata": {
                "staging_records": [
                    StagingRecord(
                        record_id="row-0",
                        tenant_id="org-edu",
                        payload={},
                        status=StagingStatus.REJECTED,
                        errors=["Fatal error"],
                        run_id="run-1",
                        row_index=0,
                    ),
                    StagingRecord(
                        record_id="row-1",
                        tenant_id="org-edu",
                        payload={},
                        status=StagingStatus.REJECTED,
                        errors=["Second error"],
                        run_id="run-1",
                        row_index=1,
                    ),
                ]
            },
        }

        lineage = tracker.track(context)
        assert len(lineage) == 3
        # First two should be the failed records
        failed_ids = {r.record_id for r in lineage if r.accumulated_errors}
        assert "row-0" in failed_ids
        assert "row-1" in failed_ids

    def test_strict_reconciliation_balanced(self):
        strategy = StrictReconciliationStrategy()
        context = {
            "tenant_id": "org-edu",
            "run_id": "run-100",
            "metadata": {
                "mapping_audit": {
                    "total_processed": 100,
                    "total_mapped": 95,
                    "failed_count": 5,
                },
                "staging_audit": {
                    "total_records": 95,
                    "validated_records": 90,
                    "error_records": 5,
                },
                "import_audit": {
                    "total_items": 90,
                    "success_count": 90,
                    "failed_count": 0,
                },
            },
        }

        manifest = strategy.reconcile(context, [])
        assert manifest.status == ReconciliationStatus.BALANCED
        assert len(manifest.stage_metrics) == 3
        assert manifest.total_records_processed == 100
        assert manifest.total_records_successful == 90
        assert manifest.total_records_rejected == 10  # 5 + 5 + 0
        assert len(manifest.discrepancies) == 0

    def test_strict_reconciliation_critical_drop(self):
        strategy = StrictReconciliationStrategy()
        context = {
            "tenant_id": "org-edu",
            "run_id": "run-101",
            "metadata": {
                "mapping_audit": {
                    "total_processed": 100,
                    "total_mapped": 100,
                    "failed_count": 0,
                },
                "staging_audit": {
                    "total_records": 80,  # 20 records unaccounted drop!
                    "validated_records": 80,
                    "error_records": 0,
                },
            },
        }

        manifest = strategy.reconcile(context, [])
        assert manifest.status == ReconciliationStatus.CRITICAL_DROP
        assert len(manifest.discrepancies) >= 1
        assert any(
            d["type"] == "QUANTITATIVE_MISMATCH" and d["unaccounted_drop"] == 20
            for d in manifest.discrepancies
        )

    def test_strict_reconciliation_overall_conservation_violation(self):
        strategy = StrictReconciliationStrategy()
        context = {
            "tenant_id": "org-edu",
            "run_id": "run-102",
            "metadata": {
                "staging_records": [
                    StagingRecord(
                        record_id=f"r-{i}",
                        tenant_id="org-edu",
                        payload={},
                        status=StagingStatus.VALIDATED,
                        run_id="run-102",
                        row_index=i,
                    )
                    for i in range(5)
                ]
            },
        }
        # Supposing 10 items processed in total but only 5 in staging and zero rejected
        manifest = strategy.reconcile(
            context,
            [
                LineageRecord(record_id=f"r-{i}", tenant_id="org-edu")
                for i in range(10)
            ],
        )
        assert manifest.total_records_processed == 10
        # If total processed > successful + rejected -> overall violation
        assert manifest.status in (
            ReconciliationStatus.CRITICAL_DROP,
            ReconciliationStatus.DISCREPANCY_DETECTED,
        )

    def test_strict_reconciliation_tenant_isolation_violation(self):
        strategy = StrictReconciliationStrategy()
        context = {"tenant_id": "org-alpha", "run_id": "run-200", "metadata": {}}
        lineage = [
            LineageRecord(record_id="ok-1", tenant_id="org-alpha"),
            LineageRecord(record_id="bad-1", tenant_id="org-beta"),
        ]

        manifest = strategy.reconcile(context, lineage)
        assert manifest.status == ReconciliationStatus.DISCREPANCY_DETECTED
        assert any(
            d["type"] == "TENANT_ISOLATION_VIOLATION"
            and d["record_id"] == "bad-1"
            for d in manifest.discrepancies
        )

    def test_memory_audit_exporter(self):
        exporter = MemoryAuditExporter()
        manifest = PipelineManifest(
            tenant_id="org-test",
            run_id="run-xyz",
            status=ReconciliationStatus.BALANCED,
            total_records_processed=50,
            total_records_successful=50,
            total_records_rejected=0,
        )
        context = {}
        summary = exporter.export(context, manifest)

        assert "pipeline_manifest" in context["metadata"]
        assert context["metadata"]["pipeline_manifest"] is manifest
        assert summary["status"] == "BALANCED"
        assert summary["total_processed"] == 50


class TestReconciliationComponent:
    def test_reconciliation_component_happy_path(self):
        comp = ReconciliationComponent()
        context = {
            "tenant_id": "tenant-school",
            "run_id": "run-999",
            "payload": [{"id": "s-1", "name": "Student A"}],
            "metadata": {
                "mapping_audit": {
                    "total_processed": 1,
                    "total_mapped": 1,
                    "failed_count": 0,
                }
            },
        }

        out = comp.execute(context)
        assert "reconciliation_audit" in out["metadata"]
        assert "pipeline_manifest" in out["metadata"]
        manifest = out["metadata"]["pipeline_manifest"]
        assert manifest.status == ReconciliationStatus.BALANCED

    def test_reconciliation_component_invalid_context(self):
        comp = ReconciliationComponent()
        with pytest.raises(TypeError):
            comp.execute("not-a-dict")  # type: ignore


class TestProcessingResultIntegration:
    def test_processing_result_from_context_with_manifest_balanced(self):
        manifest = PipelineManifest(
            tenant_id="t1",
            run_id="r1",
            status=ReconciliationStatus.BALANCED,
            total_records_processed=10,
            total_records_successful=10,
            total_records_rejected=0,
        )
        context = {
            "payload": [{"id": 1}],
            "metadata": {"pipeline_manifest": manifest, "validation_errors": []},
        }
        res = ProcessingResult.from_context(context)
        assert res.success is True
        assert res.metadata["manifest"] is manifest

    def test_processing_result_from_context_with_manifest_critical_drop(self):
        manifest = PipelineManifest(
            tenant_id="t1",
            run_id="r1",
            status=ReconciliationStatus.CRITICAL_DROP,
            total_records_processed=10,
            total_records_successful=5,
            total_records_rejected=0,
        )
        context = {
            "payload": [{"id": 1}],
            "metadata": {"pipeline_manifest": manifest, "validation_errors": []},
        }
        res = ProcessingResult.from_context(context)
        assert res.success is False
        assert res.metadata["manifest"] is manifest


class TestReconciliationDiscovery:
    def test_discovery_auto_register_reconciliation(self):
        registry = MacRegistry()
        auto_register(registry)
        assert "reconciliation_component" in registry._components
        comp_cls = registry.get("reconciliation_component")
        assert isinstance(comp_cls, ReconciliationComponent)
