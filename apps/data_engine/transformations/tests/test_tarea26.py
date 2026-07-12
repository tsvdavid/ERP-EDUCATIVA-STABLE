# apps/data_engine/transformations/tests/test_tarea26.py
"""Comprehensive unit, integration, and Zero-ORM verification suite for TAREA 26.

Tests:
1. Contracts & DTOs (`TransformationContext`, `TransformationResult`, `Report`, `Statistics`, `Error`).
2. TransformationRegistry & Thread-Safety (`register`, `get`, multi-threading).
3. ExpressionEngine (`UPPER`, `LOWER`, `TRIM`, `CONCAT`, `COALESCE`, `SUBSTRING`, `IF`, `CASE`, `NOW`, `UUID`, `HASH`, `REGEX_REPLACE`).
4. Standard Processors (`RenameFields`, `RemoveFields`, `TypeCast`, `DefaultValue`, `Trim`, `Case`, `Regex`, `Lookup`).
5. Validation Layer (`Required`, `Regex`, `Range`, `Unique`, `Length`, `Enum`, `Custom`).
6. TransformationPipeline (`add`, `remove`, `replace`, `execute`, `rollback`, `clone`, metrics).
7. Workflow Execution Integration (`BaseTransformation.execute(MacContext)`).
8. AST Static Analysis certifying Zero-ORM compliance inside `apps/data_engine/transformations/`.
"""

import ast
import copy
import datetime
from decimal import Decimal
import os
import threading
import time
import unittest
from typing import Any, Dict, List, Optional, Type

import pytest

from apps.data_engine.components.base import MacContext
from apps.data_engine.transformations import (
    BaseTransformation,
    CustomValidator,
    DefaultValueProcessor,
    EnumValidator,
    ExpressionEngine,
    ExpressionException,
    LengthValidator,
    LowerCaseProcessor,
    LookupProcessor,
    PipelineException,
    ProcessorException,
    RangeValidator,
    RegexProcessor,
    RegexValidator,
    RemoveFieldsProcessor,
    RenameFieldsProcessor,
    RequiredValidator,
    TransformationContext,
    TransformationError,
    TransformationException,
    TransformationPipeline,
    TransformationRegistry,
    TransformationReport,
    TransformationResult,
    TransformationStatistics,
    TrimProcessor,
    TypeCastProcessor,
    UniqueValidator,
    UpperCaseProcessor,
)


# ==============================================================================
# 1. Contracts and DTOs Tests
# ==============================================================================

class TestContractsAndDTOs(unittest.TestCase):
    """Verify DTO immutability, dict serialization, and context getters."""

    def test_transformation_context_immutability_and_getter(self):
        ctx = TransformationContext(
            tenant_id="tenant_x",
            run_id="run_101",
            variables={"prefix": "PROD_"},
            metadata={"source": "api"},
        )
        self.assertEqual(ctx.tenant_id, "tenant_x")
        self.assertEqual(ctx.get_variable("prefix"), "PROD_")
        self.assertEqual(ctx.get_variable("missing", "default"), "default")
        with self.assertRaises(Exception):
            ctx.tenant_id = "tenant_y"  # Frozen

    def test_transformation_error_to_dict(self):
        err = TransformationError(
            error_code="ERR_01",
            error_message="Invalid value",
            transformation_name="test_transform",
            field_name="age",
            original_value=-5,
        )
        data = err.to_dict()
        self.assertEqual(data["error_code"], "ERR_01")
        self.assertEqual(data["field_name"], "age")
        self.assertEqual(data["original_value"], "-5")

    def test_transformation_result_and_report_serialization(self):
        err = TransformationError(
            error_code="E1",
            error_message="M1",
            transformation_name="T1",
        )
        res = TransformationResult(
            transformed_record={"id": 1, "status": "bad"},
            original_record={"id": 1, "status": "raw"},
            errors=[err],
            status="REJECTED",
        )
        stats = TransformationStatistics(
            records_processed=1,
            records_accepted=0,
            records_rejected=1,
            execution_time_ms=12.5,
            throughput_records_per_sec=80.0,
            error_count=1,
        )
        report = TransformationReport(
            results=[res],
            statistics=stats,
            errors=[err],
            success=False,
        )
        report_dict = report.to_dict()
        self.assertFalse(report_dict["success"])
        self.assertEqual(report_dict["statistics"]["records_rejected"], 1)
        self.assertEqual(len(report_dict["results"]), 1)


# ==============================================================================
# 2. Registry and Thread Safety Tests
# ==============================================================================

class DummyTransform(BaseTransformation):
    @property
    def name(self) -> str: return "dummy_tx"
    @property
    def description(self) -> str: return "Dummy"
    def can_transform(self, record: Dict[str, Any]) -> bool: return True
    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]: return dict(record)
    def validate(self, record: Dict[str, Any]) -> List[TransformationError]: return []


class TestRegistryAndThreadSafety(unittest.TestCase):
    """Verify thread-safe registration and lookups in TransformationRegistry."""

    def test_register_and_get(self):
        reg = TransformationRegistry.global_registry()
        reg.register("dummy_tx_test", DummyTransform)
        cls = reg.get("dummy_tx_test")
        self.assertEqual(cls, DummyTransform)
        self.assertIn("dummy_tx_test", reg.list_names())

    def test_get_unregistered_raises(self):
        reg = TransformationRegistry.global_registry()
        with self.assertRaises(TransformationException):
            reg.get("non_existent_transformation_xyz")

    def test_concurrent_registry_access(self):
        reg = TransformationRegistry.global_registry()
        errors: List[Exception] = []

        def worker(idx: int):
            try:
                name = f"thread_tx_{idx}"
                reg.register(name, DummyTransform)
                cls = reg.get(name)
                self.assertEqual(cls, DummyTransform)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(25)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)


# ==============================================================================
# 3. Expression Engine Tests
# ==============================================================================

class TestExpressionEngine(unittest.TestCase):
    """Verify pure Python expression evaluation across all supported functions."""

    def test_upper_lower_and_trim(self):
        rec = {"first": "  ana  ", "code": "abc"}
        self.assertEqual(ExpressionEngine.evaluate("UPPER(first)", rec), "  ANA  ")
        self.assertEqual(ExpressionEngine.evaluate("TRIM(first)", rec), "ana")
        self.assertEqual(ExpressionEngine.evaluate("LOWER(code)", rec), "abc")

    def test_concat_and_coalesce(self):
        rec = {"first": "Juan", "last": "Perez", "middle": None}
        self.assertEqual(ExpressionEngine.evaluate("CONCAT(first, ' ', last)", rec), "Juan Perez")
        self.assertEqual(ExpressionEngine.evaluate("COALESCE(middle, first, 'Default')", rec), "Juan")

    def test_substring_and_regex_replace(self):
        rec = {"code": "EDU-2026-X"}
        self.assertEqual(ExpressionEngine.evaluate("SUBSTRING(code, 0, 3)", rec), "EDU")
        self.assertEqual(ExpressionEngine.evaluate("REGEX_REPLACE(code, '-\\d{4}-', '-NEW-')", rec), "EDU-NEW-X")

    def test_if_and_case(self):
        rec = {"score": 90, "grade": "A"}
        self.assertEqual(ExpressionEngine.evaluate("IF(score, 'Pass', 'Fail')", rec), "Pass")
        # CASE via dict structure representation
        case_expr = {
            "func": "CASE",
            "args": [{"missing": "1", "grade": "Excellent"}, "Other"],
        }
        self.assertEqual(ExpressionEngine.evaluate(case_expr, rec), "Excellent")

    def test_now_uuid_and_hash(self):
        rec = {"secret": "my_password"}
        now_str = ExpressionEngine.evaluate("NOW()", rec)
        self.assertIn("-", now_str)
        uuid_str = ExpressionEngine.evaluate("UUID()", rec)
        self.assertEqual(len(uuid_str), 36)
        hash_str = ExpressionEngine.evaluate("HASH(secret)", rec)
        self.assertEqual(len(hash_str), 64)


# ==============================================================================
# 4. Standard Processors Tests
# ==============================================================================

class TestStandardProcessors(unittest.TestCase):
    """Verify field mutation, casting, trimming, case conversion, and lookups."""

    def test_rename_and_remove_fields(self):
        rec = {"old_id": 100, "temp": "discard", "name": "Maria"}
        rename = RenameFieldsProcessor({"old_id": "student_id"})
        remove = RemoveFieldsProcessor(["temp"])

        rec = rename.transform(rec)
        self.assertEqual(rec["student_id"], 100)
        self.assertNotIn("old_id", rec)

        rec = remove.transform(rec)
        self.assertNotIn("temp", rec)
        self.assertEqual(rec["name"], "Maria")

    def test_type_cast_processor(self):
        rec = {
            "age": "21",
            "gpa": "3.85",
            "active": "true",
            "enrolled_date": "2026-07-12",
        }
        caster = TypeCastProcessor({
            "age": "int",
            "gpa": "Decimal",
            "active": "bool",
            "enrolled_date": "date",
        })
        transformed = caster.transform(rec)
        self.assertEqual(transformed["age"], 21)
        self.assertEqual(transformed["gpa"], Decimal("3.85"))
        self.assertTrue(transformed["active"])
        self.assertEqual(transformed["enrolled_date"], datetime.date(2026, 7, 12))

    def test_type_cast_processor_invalid_value_records_error(self):
        rec = {"age": "invalid_num"}
        caster = TypeCastProcessor({"age": "int"})
        errors = caster.validate(rec)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].error_code, "TYPE_CAST_ERROR")

    def test_default_value_trim_and_case_processors(self):
        rec = {"name": "   carlos   ", "city": None}
        default_proc = DefaultValueProcessor({"city": "Bogota", "status": "NEW"})
        trim_proc = TrimProcessor(["name"])
        upper_proc = UpperCaseProcessor(["name"])

        rec = default_proc.transform(rec)
        self.assertEqual(rec["city"], "Bogota")
        self.assertEqual(rec["status"], "NEW")

        rec = trim_proc.transform(rec)
        self.assertEqual(rec["name"], "carlos")

        rec = upper_proc.transform(rec)
        self.assertEqual(rec["name"], "CARLOS")

    def test_regex_and_lookup_processors(self):
        rec = {"phone": "+57 (310) 123-4567", "gender_code": "M"}
        regex_proc = RegexProcessor("phone", r"[\(\)\-\s\+]", "")
        lookup_proc = LookupProcessor("gender_code", {"M": "Masculino", "F": "Femenino"}, target_field="gender", default="Otro")

        rec = regex_proc.transform(rec)
        self.assertEqual(rec["phone"], "573101234567")

        rec = lookup_proc.transform(rec)
        self.assertEqual(rec["gender"], "Masculino")


# ==============================================================================
# 5. Validation Layer Tests
# ==============================================================================

class TestValidationLayer(unittest.TestCase):
    """Verify field presence, format, range, uniqueness, length, enum, and custom checks."""

    def test_required_validator(self):
        validator = RequiredValidator(["id", "name"])
        self.assertEqual(len(validator.validate({"id": 1, "name": "Ana"})), 0)
        errors = validator.validate({"id": 1, "name": "   "})
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].error_code, "REQUIRED_FIELD_MISSING")

    def test_regex_and_range_validators(self):
        regex_val = RegexValidator("email", r"^[\w\.\-]+@[\w\-]+\.[a-zA-Z]{2,}$")
        range_val = RangeValidator("score", min_val=0, max_val=100)

        self.assertEqual(len(regex_val.validate({"email": "admin@eduka360.com"})), 0)
        self.assertEqual(len(regex_val.validate({"email": "invalid_email"})), 1)

        self.assertEqual(len(range_val.validate({"score": 85})), 0)
        self.assertEqual(len(range_val.validate({"score": 105})), 1)

    def test_unique_validator(self):
        unique_val = UniqueValidator("code")
        self.assertEqual(len(unique_val.validate({"code": "MATH101"})), 0)
        self.assertEqual(len(unique_val.validate({"code": "SCI201"})), 0)
        errors = unique_val.validate({"code": "MATH101"})
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].error_code, "DUPLICATE_VALUE")
        unique_val.reset()
        self.assertEqual(len(unique_val.validate({"code": "MATH101"})), 0)

    def test_length_enum_and_custom_validators(self):
        len_val = LengthValidator("username", min_len=4, max_len=12)
        enum_val = EnumValidator("role", ["admin", "teacher", "student"])
        custom_val = CustomValidator(
            lambda rec: [
                TransformationError("CUSTOM_ERR", "Grade < 0 not allowed", "custom_grade_check", "grade", rec.get("grade"))
            ] if rec.get("grade", 0) < 0 else []
        )

        self.assertEqual(len(len_val.validate({"username": "ana_g"})), 0)
        self.assertEqual(len(len_val.validate({"username": "ab"})), 1)

        self.assertEqual(len(enum_val.validate({"role": "teacher"})), 0)
        self.assertEqual(len(enum_val.validate({"role": "hacker"})), 1)

        self.assertEqual(len(custom_val.validate({"grade": 10})), 0)
        self.assertEqual(len(custom_val.validate({"grade": -2})), 1)


# ==============================================================================
# 6. Transformation Pipeline Tests
# ==============================================================================

class TestTransformationPipeline(unittest.TestCase):
    """Verify sequential composition, rollback, cloning, and statistical reporting."""

    def test_pipeline_add_remove_replace(self):
        pipeline = TransformationPipeline("etl_pipe")
        p1 = TrimProcessor(["name"])
        p2 = UpperCaseProcessor(["name"])
        p3 = LowerCaseProcessor(["name"])

        pipeline.add(p1).add(p2)
        self.assertEqual(len(pipeline.transformations), 2)

        pipeline.replace("uppercase", p3)
        self.assertEqual(pipeline.transformations[1].name, "lowercase")

        pipeline.remove("trim")
        self.assertEqual(len(pipeline.transformations), 1)
        self.assertEqual(pipeline.transformations[0].name, "lowercase")

    def test_pipeline_execute_and_statistics(self):
        pipeline = TransformationPipeline("clean_students")
        pipeline.add(RequiredValidator(["id", "name"]))
        pipeline.add(TrimProcessor(["name", "city"]))
        pipeline.add(UpperCaseProcessor(["name"]))
        pipeline.add(DefaultValueProcessor({"city": "BOGOTA"}))

        records = [
            {"id": 1, "name": "  carlos  ", "city": "cali"},
            {"id": 2, "name": "maria", "city": None},
            {"id": None, "name": "bad_record"},  # Missing required ID -> REJECTED
            {"id": 4, "name": "CARLOS", "city": "BOGOTA"},  # UNCHANGED
        ]

        report = pipeline.execute(records)
        self.assertEqual(report.statistics.records_processed, 4)
        self.assertEqual(report.statistics.records_accepted, 3)
        self.assertEqual(report.statistics.records_rejected, 1)
        self.assertGreaterEqual(report.statistics.execution_time_ms, 0.0)
        self.assertGreater(report.statistics.throughput_records_per_sec, 0.0)

        # Check results statuses
        self.assertEqual(report.results[0].status, "MODIFIED")
        self.assertEqual(report.results[0].transformed_record["name"], "CARLOS")
        self.assertEqual(report.results[1].status, "MODIFIED")
        self.assertEqual(report.results[1].transformed_record["city"], "BOGOTA")
        self.assertEqual(report.results[2].status, "REJECTED")
        self.assertEqual(report.results[3].status, "UNCHANGED")

    def test_pipeline_rollback_and_clone(self):
        pipeline = TransformationPipeline("rollback_pipe")
        pipeline.add(RenameFieldsProcessor({"x": "y"}))

        records = [{"id": 1, "x": 10}, {"id": 2, "x": 20}]
        report = pipeline.execute(records)
        self.assertEqual(report.results[0].transformed_record, {"id": 1, "y": 10})

        reverted = pipeline.rollback()
        self.assertEqual(reverted, [{"id": 1, "x": 10}, {"id": 2, "x": 20}])

        clone_pipe = pipeline.clone()
        self.assertEqual(clone_pipe.name, "rollback_pipe_clone")
        self.assertEqual(len(clone_pipe.transformations), 1)
        self.assertIsNot(clone_pipe.transformations[0], pipeline.transformations[0])


# ==============================================================================
# 7. Workflow Execution Integration Tests
# ==============================================================================

class TestWorkflowExecutionIntegration(unittest.TestCase):
    """Verify BaseTransformation.execute(MacContext) inside a standard pipeline."""

    def test_execute_in_mac_context_with_records_list(self):
        context: MacContext = {
            "tenant_id": "tenant_1",
            "run_id": "run_tx_1",
            "payload": {
                "records": [
                    {"code": "  abc  ", "val": 10},
                    {"code": "  def  ", "val": 20},
                ]
            },
        }
        processor = TrimProcessor(["code"])
        out = processor.execute(context)
        self.assertIn("payload", out)
        recs = out["payload"]["records"]
        self.assertEqual(recs[0]["code"], "abc")
        self.assertEqual(recs[1]["code"], "def")


# ==============================================================================
# 8. Zero-ORM Compliance AST Inspection
# ==============================================================================

class TestZeroOrmComplianceInTransformations(unittest.TestCase):
    """Perform static AST verification to guarantee Zero-ORM in `transformations/`."""

    def test_transformations_package_has_no_django_orm_dependencies(self):
        forbidden_modules = {"django.db", "django.db.models", "django.db.transaction"}
        forbidden_names = {"models", "QuerySet", "atomic"}

        package_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        for root, _, files in os.walk(package_dir):
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
