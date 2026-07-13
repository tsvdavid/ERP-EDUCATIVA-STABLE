# apps/data_engine/quality/tests/test_tarea29.py
"""Comprehensive suite of tests for the Data Quality Rules Engine & Governance subsystem."""

import ast
import os
import unittest
from typing import Any, Dict, List

from apps.data_engine.events.dispatcher import EventDispatcher
from apps.data_engine.events.models import EventCategory, EventEnvelope
from apps.data_engine.events.registry import EventBusRegistry
from apps.data_engine.progress.registry import ProgressRegistry
from apps.data_engine.progress.tracker import ProgressTracker
from apps.data_engine.transformations.contracts import TransformationContext
from apps.data_engine.transformations.pipeline import TransformationPipeline

from apps.data_engine.quality.exceptions import QualityException, RuleException
from apps.data_engine.quality.models import QualityViolation, QualityStatistics
from apps.data_engine.quality.registry import QualityRuleRegistry
from apps.data_engine.quality.scorer import QualityScorer
from apps.data_engine.quality.reporters import (
    JsonQualityReporter,
    CsvQualityReporter,
    SummaryQualityReporter,
)
from apps.data_engine.quality.engine import (
    QualityEngine,
    QualityRuleTransformationAdapter,
    QualityWorkflowComponent,
)
from apps.data_engine.quality.rules import (
    RequiredRule,
    RegexRule,
    RangeRule,
    EnumRule,
    UniqueRule,
    LengthRule,
    EmailRule,
    DateRule,
    NumericRule,
    ReferenceRule,
    CompositeRule,
    ConditionalRule,
)


class TestQualityModelsAndRegistry(unittest.TestCase):
    """Test public registry and models behavior."""

    def setUp(self) -> None:
        self.registry = QualityRuleRegistry.global_registry()
        self.registry.reset()

    def test_registry_registration_and_retrieval(self) -> None:
        rule = RequiredRule("email")
        self.registry.register(rule)
        
        retrieved = self.registry.get(rule.code)
        self.assertEqual(retrieved.code, "REQUIRED_EMAIL")
        self.assertEqual(retrieved.field, "email")
        self.assertEqual(retrieved.severity, "ERROR")

        rules_list = self.registry.list_rules()
        self.assertEqual(len(rules_list), 1)
        
        self.registry.remove(rule.code)
        self.assertEqual(len(self.registry.list_rules()), 0)

    def test_registry_duplicate_raises(self) -> None:
        rule = RequiredRule("email")
        self.registry.register(rule)
        
        with self.assertRaises(ValueError):
            self.registry.register(rule, overwrite=False)

    def test_violation_serialization(self) -> None:
        v = QualityViolation(
            rule_code="TEST_RULE",
            field="age",
            message="Invalid age",
            severity="WARNING",
            value="abc",
        )
        d = v.to_dict()
        self.assertEqual(d["rule_code"], "TEST_RULE")
        self.assertEqual(d["field"], "age")
        self.assertEqual(d["message"], "Invalid age")
        self.assertEqual(d["severity"], "WARNING")
        self.assertEqual(d["value"], "abc")


class TestBuiltinQualityRules(unittest.TestCase):
    """Test all 12 builtin quality rules."""

    def test_required_rule(self) -> None:
        rule = RequiredRule("name", severity="CRITICAL")
        self.assertEqual(rule.code, "REQUIRED_NAME")
        
        # Valid
        self.assertEqual(len(rule.validate({"name": "Juan"})), 0)
        # Missing
        violations = rule.validate({})
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, "CRITICAL")
        # Empty/whitespace
        self.assertEqual(len(rule.validate({"name": "   "})), 1)

    def test_regex_rule(self) -> None:
        rule = RegexRule("phone", pattern=r"^\+\d{2,3}-\d{9}$")
        self.assertEqual(rule.code, "REGEX_PHONE")
        
        # Valid phone
        self.assertEqual(len(rule.validate({"phone": "+34-666777888"})), 0)
        # Empty values should pass (use RequiredRule to check presence)
        self.assertEqual(len(rule.validate({"phone": ""})), 0)
        # Invalid format
        self.assertEqual(len(rule.validate({"phone": "666777888"})), 1)

    def test_range_rule(self) -> None:
        rule = RangeRule("grade", min_value=0.0, max_value=10.0)
        
        self.assertEqual(len(rule.validate({"grade": 5})), 0)
        self.assertEqual(len(rule.validate({"grade": 0})), 0)
        self.assertEqual(len(rule.validate({"grade": 10.0})), 0)
        
        # Under min
        self.assertEqual(len(rule.validate({"grade": -1})), 1)
        # Over max
        self.assertEqual(len(rule.validate({"grade": 10.1})), 1)
        # Non-numeric
        self.assertEqual(len(rule.validate({"grade": "abc"})), 1)

    def test_enum_rule(self) -> None:
        rule = EnumRule("status", allowed_values=["active", "inactive"])
        
        self.assertEqual(len(rule.validate({"status": "active"})), 0)
        self.assertEqual(len(rule.validate({"status": "inactive"})), 0)
        self.assertEqual(len(rule.validate({"status": "pending"})), 1)

    def test_unique_rule(self) -> None:
        rule = UniqueRule("id_card")
        ctx: Dict[str, Any] = {}
        
        self.assertEqual(len(rule.validate({"id_card": "12345"}, ctx)), 0)
        self.assertEqual(len(rule.validate({"id_card": "54321"}, ctx)), 0)
        # Duplicate
        self.assertEqual(len(rule.validate({"id_card": "12345"}, ctx)), 1)

    def test_length_rule(self) -> None:
        rule = LengthRule("username", min_length=4, max_length=8)
        
        self.assertEqual(len(rule.validate({"username": "juan"})), 0)
        self.assertEqual(len(rule.validate({"username": "maria12"})), 0)
        # Under min
        self.assertEqual(len(rule.validate({"username": "bob"})), 1)
        # Over max
        self.assertEqual(len(rule.validate({"username": "maria_del_carmen"})), 1)

    def test_email_rule(self) -> None:
        rule = EmailRule("email")
        
        self.assertEqual(len(rule.validate({"email": "test@eduka360.com"})), 0)
        self.assertEqual(len(rule.validate({"email": "invalid-email"})), 1)

    def test_date_rule(self) -> None:
        rule = DateRule("birth_date", format_str="%Y-%m-%d")
        
        self.assertEqual(len(rule.validate({"birth_date": "2000-01-01"})), 0)
        self.assertEqual(len(rule.validate({"birth_date": "01/01/2000"})), 1)

    def test_numeric_rule(self) -> None:
        rule = NumericRule("salary")
        
        self.assertEqual(len(rule.validate({"salary": "1200.50"})), 0)
        self.assertEqual(len(rule.validate({"salary": 1000})), 0)
        self.assertEqual(len(rule.validate({"salary": "1,000"})), 1)

    def test_reference_rule(self) -> None:
        rule = ReferenceRule("course_id", allowed_references={"MAT-1", "FIS-2"})
        
        self.assertEqual(len(rule.validate({"course_id": "MAT-1"})), 0)
        self.assertEqual(len(rule.validate({"course_id": "MAT-9"})), 1)

    def test_composite_rule(self) -> None:
        rule = CompositeRule([
            RequiredRule("code"),
            LengthRule("code", min_length=2, max_length=4),
        ])
        
        self.assertEqual(len(rule.validate({"code": "ABC"})), 0)
        # Triggers LengthRule violation
        self.assertEqual(len(rule.validate({"code": "A"})), 1)
        # Triggers RequiredRule violation
        self.assertEqual(len(rule.validate({})), 1)

    def test_conditional_rule(self) -> None:
        rule = ConditionalRule(
            condition=lambda rec: rec.get("role") == "student",
            rule=RequiredRule("student_code"),
        )
        
        # Condition matches, student_code missing -> violation
        self.assertEqual(len(rule.validate({"role": "student"})), 1)
        # Condition matches, student_code present -> passes
        self.assertEqual(len(rule.validate({"role": "student", "student_code": "ST-1"})), 0)
        # Condition mismatches (not student), student_code missing -> passes
        self.assertEqual(len(rule.validate({"role": "teacher"})), 0)


class TestQualityScorerAndReporters(unittest.TestCase):
    """Test scoring math deductions and reporters formatting."""

    def test_scorer_severity_deductions(self) -> None:
        scorer = QualityScorer()
        
        # Perfect
        self.assertEqual(scorer.calculate_record_score([]), 100.0)
        
        # Deductions
        v_info = QualityViolation("R1", "f", "info message", "INFO")
        v_warn = QualityViolation("R2", "f", "warn message", "WARNING")
        v_err = QualityViolation("R3", "f", "error message", "ERROR")
        v_crit = QualityViolation("R4", "f", "critical message", "CRITICAL")
        
        self.assertEqual(scorer.calculate_record_score([v_info]), 99.0)
        self.assertEqual(scorer.calculate_record_score([v_warn]), 90.0)
        self.assertEqual(scorer.calculate_record_score([v_err]), 70.0)
        self.assertEqual(scorer.calculate_record_score([v_crit]), 0.0)
        
        # Compound deductions
        self.assertEqual(scorer.calculate_record_score([v_info, v_warn]), 89.0)
        # Floor capped at 0.0
        self.assertEqual(scorer.calculate_record_score([v_err, v_err, v_err, v_err]), 0.0)

    def test_scorer_aggregate_and_rating(self) -> None:
        scorer = QualityScorer()
        
        self.assertEqual(scorer.determine_rating(95.0), "EXCELLENT")
        self.assertEqual(scorer.determine_rating(85.0), "GOOD")
        self.assertEqual(scorer.determine_rating(65.0), "FAIR")
        self.assertEqual(scorer.determine_rating(45.0), "POOR")
        
        self.assertEqual(scorer.calculate_aggregate_score([100.0, 50.0]), 75.0)
        self.assertEqual(scorer.calculate_aggregate_score([]), 100.0)

    def test_reporters(self) -> None:
        stats = QualityStatistics(
            total_records=2,
            passed_records=1,
            failed_records=1,
            total_violations=2,
            info_count=0,
            warning_count=1,
            error_count=1,
            critical_count=0,
            execution_time_ms=5.0,
            rules_executed=2,
        )
        from apps.data_engine.quality.models import QualityScore, QualityReport
        score = QualityScore(score=80.0, rating="GOOD")
        violations = {
            1: [
                QualityViolation("R1", "f", "Error message", "ERROR", "val1"),
                QualityViolation("R2", "g", "Warn message", "WARNING", "val2"),
            ]
        }
        report = QualityReport("session-1", "TPL-1", stats, score, violations, "2026-07-13")

        # JSON Reporter
        json_str = JsonQualityReporter().generate(report)
        self.assertIn("session-1", json_str)
        self.assertIn("TPL-1", json_str)
        
        # CSV Reporter
        csv_str = CsvQualityReporter().generate(report)
        self.assertIn("record_index,rule_code,field,severity,message,value", csv_str)
        self.assertIn("1,R1,f,ERROR,Error message,val1", csv_str)
        
        # Summary Reporter
        summary_str = SummaryQualityReporter().generate(report)
        self.assertIn("DATA QUALITY EXECUTIVE SUMMARY", summary_str)
        self.assertIn("Quality Score:   80.00% (GOOD)", summary_str)


from apps.data_engine.events.base import BaseEventSubscriber

class TestQualityEngineAndAdapters(unittest.TestCase):
    """Test the complete quality engine execution and integration adapters."""

    def test_engine_executes_rules_and_notifies(self) -> None:
        # Set up registries and dispatcher
        dispatcher = EventDispatcher()
        EventBusRegistry.global_registry().reset()
        EventBusRegistry.global_registry()._dispatcher = dispatcher
        
        ProgressRegistry.global_registry().clear()
        tracker = ProgressTracker("test-session", total_expected_records=2)
        ProgressRegistry.global_registry().register("test-session", tracker)
        
        class MockSubscriber(BaseEventSubscriber):
            def __init__(self) -> None:
                self.envelopes: List[EventEnvelope] = []
            def accepts(self, category: EventCategory) -> bool:
                return True
            def on_event(self, envelope: EventEnvelope) -> None:
                self.envelopes.append(envelope)
        
        subscriber = MockSubscriber()
        dispatcher.subscribe(subscriber)

        # Build rules
        rules = [
            RequiredRule("name", severity="ERROR"),
            EmailRule("email", severity="WARNING"),
            RangeRule("age", min_value=18, severity="CRITICAL"),
        ]

        records = [
            {"name": "Alice", "email": "alice@eduka360.com", "age": 20},  # Passed
            {"name": "", "email": "bad-email", "age": 15},                # Rejected (Error + Critical + Warning)
        ]

        engine = QualityEngine()
        report = engine.execute(
            records=records,
            session_id="test-session",
            template_code="STUDENT_IMPORT",
            rules=rules,
        )

        # Check report stats
        self.assertEqual(report.statistics.total_records, 2)
        self.assertEqual(report.statistics.passed_records, 1)
        self.assertEqual(report.statistics.failed_records, 1)
        self.assertEqual(report.statistics.total_violations, 3)
        self.assertEqual(report.statistics.error_count, 1)
        self.assertEqual(report.statistics.critical_count, 1)
        self.assertEqual(report.statistics.warning_count, 1)

        # Check Scoring
        # Record 0 has 0 violations: score 100.
        # Record 1 has: Required (ERROR: -30), Email (WARNING: -10), Range (CRITICAL: -100). Score capped at 0.
        # Mean score: 50.0
        self.assertEqual(report.score.score, 50.0)
        self.assertEqual(report.score.rating, "FAIR")

        # Verify Progress Tracker updated
        snapshot = tracker.get_snapshot()
        self.assertEqual(snapshot.records_processed, 2)
        self.assertEqual(snapshot.records_accepted, 1)
        self.assertEqual(snapshot.records_rejected, 1)

        # Verify Event Bus notified
        self.assertEqual(len(subscriber.envelopes), 1)
        env = subscriber.envelopes[0]
        self.assertEqual(env.category, EventCategory.EXECUTION)
        self.assertEqual(env.event_type, "DATA_QUALITY_REPORT")
        self.assertEqual(env.payload["template_code"], "STUDENT_IMPORT")

    def test_rule_transformation_adapter(self) -> None:
        pipeline = TransformationPipeline("quality_pipeline")
        
        # Create unique validator rule and wrap it
        rule = UniqueRule("enrollment_id", severity="ERROR")
        adapter = QualityRuleTransformationAdapter(rule)
        pipeline.add(adapter)

        records = [
            {"enrollment_id": "ENR100"},
            {"enrollment_id": "ENR200"},
            {"enrollment_id": "ENR100"},  # Duplicate!
        ]

        report = pipeline.execute(records)
        self.assertEqual(report.statistics.records_processed, 3)
        self.assertEqual(report.statistics.records_accepted, 2)
        self.assertEqual(report.statistics.records_rejected, 1)
        self.assertEqual(len(report.errors), 1)
        self.assertEqual(report.errors[0].error_code, "UNIQUE_ENROLLMENT_ID")

    def test_workflow_component_split_and_attachment(self) -> None:
        engine = QualityEngine()
        rules = [RequiredRule("role")]
        
        comp = QualityWorkflowComponent(
            engine=engine,
            rules=rules,
            template_code="TEST_FLOW",
        )

        context: Dict[str, Any] = {
            "run_id": "flow-session-123",
            "payload": {
                "records": [
                    {"role": "teacher", "name": "John"},
                    {"role": "", "name": "Unknown"},
                ]
            }
        }

        res = comp.execute(context)
        out_payload = res["payload"]

        # Component must split accepted and rejected records
        self.assertEqual(len(out_payload["records"]), 1)
        self.assertEqual(out_payload["records"][0]["name"], "John")
        
        self.assertEqual(len(out_payload["rejected_records"]), 1)
        self.assertEqual(out_payload["rejected_records"][0]["name"], "Unknown")

        # Quality report should be attached
        self.assertIn("quality_report", out_payload)
        report_dict = out_payload["quality_report"]
        self.assertEqual(report_dict["statistics"]["total_records"], 2)
        self.assertEqual(report_dict["statistics"]["failed_records"], 1)


class TestZeroOrmComplianceInQuality(unittest.TestCase):
    """Ensure no database dependency is imported or utilized in the quality layer."""

    def test_quality_package_has_no_django_orm_dependencies(self) -> None:
        forbidden_modules = {"django.db", "django.db.models", "django.db.transaction"}
        forbidden_names = {"models", "QuerySet", "atomic"}

        quality_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        for root, _, files in os.walk(quality_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=filepath)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            for forbidden in forbidden_modules:
                                self.assertFalse(
                                    alias.name == forbidden or alias.name.startswith(f"{forbidden}."),
                                    f"Zero-ORM violation in {filepath}: import {alias.name}",
                                )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for forbidden in forbidden_modules:
                                self.assertFalse(
                                    node.module == forbidden or node.module.startswith(f"{forbidden}."),
                                    f"Zero-ORM violation in {filepath}: from {node.module} import ...",
                                )
                    elif isinstance(node, ast.Name):
                        if node.id in forbidden_names:
                            self.assertNotEqual(
                                node.id,
                                "QuerySet",
                                f"Zero-ORM violation in {filepath}: direct use of {node.id}",
                            )
