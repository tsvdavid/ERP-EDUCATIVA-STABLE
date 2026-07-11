# apps/data_engine/components/reconciliation/strategies.py
"""Concrete reconciliation strategies, lineage trackers, and audit exporters for MAC.

Defines:
- ``StandardLineageTracker``: Reconstructs record lineage from context metadata across all stages.
- ``StrictReconciliationStrategy``: Audits quantitative conservation and multi-tenant integrity.
- ``MemoryAuditExporter``: Attaches the manifest to context metadata and produces audit summary.
"""

from typing import Any, Dict, List, Optional, Set

from apps.data_engine.components.importers.models import ImportResult, ImportStatus
from apps.data_engine.components.exporters.models import ExportResult, ExportStatus
from apps.data_engine.components.staging.models import StagingRecord, StagingStatus

from .base import BaseLineageTracker, BaseReconciliationStrategy, BaseAuditExporter
from .models import LineageRecord, PipelineManifest, ReconciliationStatus, StageMetric


class StandardLineageTracker(BaseLineageTracker):
    """Reconstructs record lineage by inspecting metadata audit logs and objects across stages.

    Mitigates excessive memory consumption (R-01) by capping lineage_summary length
    and prioritizing failed/rejected records plus a representative sample of successes.
    """

    def __init__(self, max_records_summary: int = 5000):
        self._max_records_summary = max_records_summary

    def track(self, context: Dict[str, Any]) -> List[LineageRecord]:
        """Inspect context and trace distinct record IDs across stages."""
        tenant_id = context.get("tenant_id", "default")
        metadata = context.get("metadata", {})

        records_map: Dict[str, LineageRecord] = {}

        # 1. Check raw payload records
        payload = context.get("payload", [])
        if isinstance(payload, dict):
            raw_rows = payload.get("records", [])
        elif isinstance(payload, list):
            raw_rows = payload
        else:
            raw_rows = []

        for idx, row in enumerate(raw_rows):
            if isinstance(row, dict):
                rec_id = str(
                    row.get("id") or row.get("record_id") or f"payload-row-{idx}"
                )
                if rec_id not in records_map:
                    records_map[rec_id] = LineageRecord(
                        record_id=rec_id,
                        tenant_id=tenant_id,
                        stage_history=["ingestion"],
                        final_status="INGESTED",
                    )

        # 2. Check staging_records
        staging_records = metadata.get("staging_records", [])
        for rec in staging_records:
            if isinstance(rec, StagingRecord):
                r_id = str(rec.record_id)
                if r_id not in records_map:
                    records_map[r_id] = LineageRecord(
                        record_id=r_id,
                        tenant_id=str(rec.tenant_id),
                        stage_history=["ingestion", "staging"],
                        final_status=str(rec.status.value),
                    )
                else:
                    if "staging" not in records_map[r_id].stage_history:
                        records_map[r_id].stage_history.append("staging")
                    records_map[r_id].final_status = str(rec.status.value)
                    records_map[r_id].tenant_id = str(rec.tenant_id)

                if rec.status == StagingStatus.REJECTED and rec.errors:
                    for err in rec.errors:
                        err_str = (
                            err.get("message", str(err))
                            if isinstance(err, dict)
                            else str(err)
                        )
                        records_map[r_id].accumulated_errors.append(
                            f"[staging] {err_str}"
                        )

        # 3. Check import_result
        import_res = metadata.get("import_result")
        if isinstance(import_res, ImportResult):
            for item in import_res.items:
                r_id = str(item.record_id)
                if r_id not in records_map:
                    records_map[r_id] = LineageRecord(
                        record_id=r_id,
                        tenant_id=str(item.tenant_id),
                        stage_history=["import"],
                        final_status=str(item.status.value),
                    )
                else:
                    if "import" not in records_map[r_id].stage_history:
                        records_map[r_id].stage_history.append("import")
                    records_map[r_id].final_status = str(item.status.value)
                    records_map[r_id].tenant_id = str(item.tenant_id)

                if item.status == ImportStatus.FAILED and item.error:
                    records_map[r_id].accumulated_errors.append(
                        f"[import] {item.error}"
                    )

        # 4. Check export_result
        export_res = metadata.get("export_result")
        if isinstance(export_res, ExportResult):
            for item in export_res.items:
                r_id = str(item.record_id)
                if r_id not in records_map:
                    records_map[r_id] = LineageRecord(
                        record_id=r_id,
                        tenant_id=str(item.tenant_id),
                        stage_history=["export"],
                        final_status=str(item.status.value),
                    )
                else:
                    if "export" not in records_map[r_id].stage_history:
                        records_map[r_id].stage_history.append("export")
                    records_map[r_id].final_status = str(item.status.value)
                    records_map[r_id].tenant_id = str(item.tenant_id)

                if item.status == ExportStatus.FAILED and item.error:
                    records_map[r_id].accumulated_errors.append(
                        f"[export] {item.error}"
                    )

        all_records = list(records_map.values())

        # If summary limit exceeded, prioritize errors/failures
        if len(all_records) > self._max_records_summary:
            failed_recs = [
                r
                for r in all_records
                if r.accumulated_errors
                or r.final_status in ("REJECTED", "FAILED", "ERROR")
            ]
            success_recs = [
                r
                for r in all_records
                if not r.accumulated_errors
                and r.final_status not in ("REJECTED", "FAILED", "ERROR")
            ]
            remaining_slots = max(0, self._max_records_summary - len(failed_recs))
            return failed_recs + success_recs[:remaining_slots]

        return all_records


class StrictReconciliationStrategy(BaseReconciliationStrategy):
    """Audits quantitative conservation across pipeline stages and multi-tenant isolation.

    Enforces conservation law: Items In = Items Out + Items Rejected.
    Any unexplained drop triggers a CRITICAL_DROP status.
    """

    def reconcile(
        self, context: Dict[str, Any], lineage: List[LineageRecord]
    ) -> PipelineManifest:
        """Execute reconciliation checks and build immutable manifest."""
        tenant_id = context.get("tenant_id", "default")
        run_id = context.get("run_id", "unknown")
        metadata = context.get("metadata", {})

        discrepancies: List[Dict[str, Any]] = []
        stage_metrics: List[StageMetric] = []

        # 1. Check tenant isolation across lineage records
        for rec in lineage:
            if rec.tenant_id != tenant_id and rec.tenant_id != "default":
                discrepancies.append({
                    "type": "TENANT_ISOLATION_VIOLATION",
                    "record_id": rec.record_id,
                    "record_tenant_id": rec.tenant_id,
                    "expected_tenant_id": tenant_id,
                    "message": (
                        f"Record {rec.record_id} belongs to tenant {rec.tenant_id} "
                        f"but pipeline run belongs to {tenant_id}"
                    ),
                })

        # 2. Extract stage-by-stage quantitative metrics
        # Mapping / Casting / Schema Validation audit
        if "mapping_audit" in metadata:
            m_aud = metadata["mapping_audit"]
            stage_metrics.append(
                StageMetric(
                    stage_name="mapping",
                    items_in=m_aud.get("total_processed", 0),
                    items_out=m_aud.get("total_mapped", 0),
                    items_rejected=m_aud.get("failed_count", 0),
                )
            )

        if "staging_audit" in metadata:
            s_aud = metadata["staging_audit"]
            stage_metrics.append(
                StageMetric(
                    stage_name="staging",
                    items_in=s_aud.get("total_records", 0),
                    items_out=s_aud.get("validated_records", 0),
                    items_rejected=s_aud.get("error_records", 0),
                )
            )
        elif "staging_records" in metadata:
            recs = metadata["staging_records"]
            val_c = sum(
                1
                for r in recs
                if isinstance(r, StagingRecord) and r.status == StagingStatus.VALIDATED
            )
            rej_c = sum(
                1
                for r in recs
                if isinstance(r, StagingRecord) and r.status == StagingStatus.REJECTED
            )
            stage_metrics.append(
                StageMetric(
                    stage_name="staging",
                    items_in=len(recs),
                    items_out=val_c,
                    items_rejected=rej_c,
                )
            )

        if "import_audit" in metadata:
            i_aud = metadata["import_audit"]
            stage_metrics.append(
                StageMetric(
                    stage_name="import",
                    items_in=i_aud.get("total_items", 0),
                    items_out=i_aud.get("success_count", 0),
                    items_rejected=i_aud.get("failed_count", 0),
                )
            )

        if "export_audit" in metadata:
            e_aud = metadata["export_audit"]
            stage_metrics.append(
                StageMetric(
                    stage_name="export",
                    items_in=e_aud.get("total_items", 0),
                    items_out=e_aud.get("exported_count", 0),
                    items_rejected=e_aud.get("failed_count", 0),
                )
            )

        # 3. Check conservation law between consecutive stages
        for i in range(len(stage_metrics) - 1):
            prev = stage_metrics[i]
            curr = stage_metrics[i + 1]
            if curr.items_in != prev.items_out:
                diff = prev.items_out - curr.items_in
                discrepancies.append({
                    "type": "QUANTITATIVE_MISMATCH",
                    "from_stage": prev.stage_name,
                    "to_stage": curr.stage_name,
                    "prev_out": prev.items_out,
                    "curr_in": curr.items_in,
                    "unaccounted_drop": diff,
                    "message": (
                        f"Unaccounted drop of {diff} records between "
                        f"{prev.stage_name} (out: {prev.items_out}) and "
                        f"{curr.stage_name} (in: {curr.items_in})"
                    ),
                })

        # Calculate overall totals
        total_processed = max(
            stage_metrics[0].items_in if stage_metrics else 0,
            len(lineage)
        )
        total_successful = (
            stage_metrics[-1].items_out
            if stage_metrics
            else sum(1 for r in lineage if not r.accumulated_errors)
        )
        total_rejected = sum(sm.items_rejected for sm in stage_metrics)
        if not stage_metrics:
            total_rejected = sum(1 for r in lineage if r.accumulated_errors)

        # Check overall conservation check: processed == successful + rejected across single or chained stage
        if total_processed > 0 and total_processed > (total_successful + total_rejected):
            unaccounted = total_processed - (total_successful + total_rejected)
            discrepancies.append({
                "type": "OVERALL_CONSERVATION_VIOLATION",
                "total_processed": total_processed,
                "total_successful": total_successful,
                "total_rejected": total_rejected,
                "unaccounted_records": unaccounted,
                "message": (
                    f"Overall pipeline balance violation: {unaccounted} records "
                    f"dropped without rejection audit or success state."
                ),
            })

        # Determine overall reconciliation status
        status = ReconciliationStatus.BALANCED
        if not stage_metrics and not lineage:
            status = ReconciliationStatus.UNPROCESSED
        elif any(
            d.get("type")
            in ("QUANTITATIVE_MISMATCH", "OVERALL_CONSERVATION_VIOLATION")
            and d.get("unaccounted_drop", d.get("unaccounted_records", 0)) > 0
            for d in discrepancies
        ):
            status = ReconciliationStatus.CRITICAL_DROP
        elif discrepancies:
            status = ReconciliationStatus.DISCREPANCY_DETECTED

        return PipelineManifest(
            tenant_id=tenant_id,
            run_id=run_id,
            status=status,
            total_records_processed=total_processed,
            total_records_successful=total_successful,
            total_records_rejected=total_rejected,
            stage_metrics=stage_metrics,
            lineage_summary=lineage,
            discrepancies=discrepancies,
        )


class MemoryAuditExporter(BaseAuditExporter):
    """Exports the audit manifest by attaching it to context metadata.

    Returns a flat summary dictionary for immediate monitoring and observability.
    """

    def export(
        self, context: Dict[str, Any], manifest: PipelineManifest
    ) -> Dict[str, Any]:
        """Attach manifest and return audit summary."""
        if "metadata" not in context:
            context["metadata"] = {}

        context["metadata"]["pipeline_manifest"] = manifest

        return {
            "manifest_id": manifest.manifest_id,
            "status": manifest.status.value,
            "total_processed": manifest.total_records_processed,
            "total_successful": manifest.total_records_successful,
            "total_rejected": manifest.total_records_rejected,
            "discrepancies_count": len(manifest.discrepancies),
            "timestamp": manifest.timestamp,
        }


__all__ = [
    "StandardLineageTracker",
    "StrictReconciliationStrategy",
    "MemoryAuditExporter",
]
