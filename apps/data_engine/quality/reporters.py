# apps/data_engine/quality/reporters.py
"""Implementations of data quality report generators in JSON, CSV and Summary text formats."""

import csv
import io
import json
from apps.data_engine.quality.base import BaseQualityReporter
from apps.data_engine.quality.models import QualityReport


class JsonQualityReporter(BaseQualityReporter):
    """Generates detailed JSON quality reports."""

    def generate(self, report: QualityReport) -> str:
        return json.dumps(report.to_dict(), indent=2)


class CsvQualityReporter(BaseQualityReporter):
    """Generates detailed CSV reports of quality violations."""

    def generate(self, report: QualityReport) -> str:
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        
        # CSV Headers
        writer.writerow(["record_index", "rule_code", "field", "severity", "message", "value"])
        
        for rec_idx, violations in report.violations_by_record.items():
            for v in violations:
                writer.writerow([
                    rec_idx,
                    v.rule_code,
                    v.field or "",
                    v.severity,
                    v.message,
                    str(v.value) if v.value is not None else "",
                ])
                
        return output.getvalue()


class SummaryQualityReporter(BaseQualityReporter):
    """Generates human-readable plain text executive summaries."""

    def generate(self, report: QualityReport) -> str:
        stats = report.statistics
        score = report.score
        lines = [
            "==================================================",
            "           DATA QUALITY EXECUTIVE SUMMARY         ",
            "==================================================",
            f"Session ID:      {report.session_id}",
            f"Template:        {report.template_code}",
            f"Timestamp:       {report.created_at}",
            "--------------------------------------------------",
            f"Quality Score:   {score.score:.2f}% ({score.rating})",
            "--------------------------------------------------",
            f"Total Records:   {stats.total_records}",
            f"Passed Records:  {stats.passed_records}",
            f"Failed Records:  {stats.failed_records}",
            f"Rules Executed:  {stats.rules_executed}",
            "--------------------------------------------------",
            "Violation Counts by Severity:",
            f"  CRITICAL:      {stats.critical_count}",
            f"  ERROR:         {stats.error_count}",
            f"  WARNING:       {stats.warning_count}",
            f"  INFO:          {stats.info_count}",
            f"  Total:         {stats.total_violations}",
            "==================================================",
        ]
        return "\n".join(lines)
