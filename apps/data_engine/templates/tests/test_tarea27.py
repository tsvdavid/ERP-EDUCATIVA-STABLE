# apps/data_engine/templates/tests/test_tarea27.py
"""Comprehensive unit, integration, and Zero-ORM verification suite for TAREA 27.

Tests:
1. Contracts & Models (`TemplateVersion`, `ColumnDefinition`, `TemplateDefinition`, `ImportPipelineDefinition`, `TemplateContext`, `TemplateValidationError`).
2. TemplateRegistry (`register`, `get`, `list_templates`, `set_active_version`, `remove`, multi-threaded concurrency).
3. TemplatePipelineBuilder (`build_connector`, `build_transformation_pipeline`, `validate_execution_readiness`, error handling).
4. Standard Enterprise Templates (`StudentEnrollmentTemplate`, `FinancialFeeTemplate` execution and validation).
5. AST Static Analysis certifying Zero-ORM compliance inside `apps/data_engine/templates/`.
"""

import ast
from decimal import Decimal
import os
import threading
import unittest
from typing import Any, Dict, List, Optional

import pytest

from apps.data_engine.connectors import BaseConnector, ConnectorRegistry
from apps.data_engine.transformations import TransformationPipeline
from apps.data_engine.templates import (
    BaseImportTemplate,
    ColumnDefinition,
    ConnectorDefinition,
    FinancialFeeTemplate,
    ImportPipelineDefinition,
    LoaderDefinition,
    StudentEnrollmentTemplate,
    TemplateBuildException,
    TemplateContext,
    TemplateDefinition,
    TemplateException,
    TemplateNotFoundException,
    TemplatePipelineBuilder,
    TemplateRegistry,
    TemplateValidationError,
    TemplateValidationException,
    TemplateVersion,
    TransformationDefinition,
    ValidatorDefinition,
    VersionConflictException,
)


# ==============================================================================
# Dummy Template for Testing
# ==============================================================================

class DummyTemplate(BaseImportTemplate):
    def __init__(self, code_name: str = "dummy", ver: str = "1.0.0", status: str = "ACTIVE") -> None:
        super().__init__()
        self._code = code_name
        self._ver = TemplateVersion.parse(ver, status=status)

    @property
    def code(self) -> str:
        return self._code

    @property
    def name(self) -> str:
        return f"Dummy Template {self._code}"

    @property
    def version(self) -> TemplateVersion:
        return self._ver

    def get_template_definition(self) -> TemplateDefinition:
        return TemplateDefinition(
            code=self.code,
            name=self.name,
            version=self.version,
            columns=[ColumnDefinition("id", "id_raw", "int", required=True)],
            target_entity="DummyEntity",
        )

    def get_pipeline_definition(self) -> ImportPipelineDefinition:
        return ImportPipelineDefinition(
            connector=ConnectorDefinition("csv", {"delimiter": ","}),
            mapping={"id_raw": "id"},
            transformations=[TransformationDefinition("trim", {"fields": ["id_raw"]})],
            validators=[ValidatorDefinition("required_validator", {"fields": ["id_raw"]})],
            loader=LoaderDefinition("default", "dummy_table"),
        )

    def validate_template(self) -> List[TemplateValidationError]:
        return []


# ==============================================================================
# 1. Contracts & Models Tests
# ==============================================================================

class TestContractsAndModels(unittest.TestCase):
    """Verify DTO immutability, semantic version parsing, and dictionary serialization."""

    def test_template_version_string_and_parsing(self):
        v = TemplateVersion(major=2, minor=1, patch=5, status="ACTIVE")
        self.assertEqual(str(v), "2.1.5")
        parsed = TemplateVersion.parse("3.0.1", status="DEPRECATED")
        self.assertEqual(parsed.major, 3)
        self.assertEqual(parsed.minor, 0)
        self.assertEqual(parsed.patch, 1)
        self.assertEqual(parsed.status, "DEPRECATED")

    def test_template_version_invalid_parsing_raises(self):
        with self.assertRaises(ValueError):
            TemplateVersion.parse("invalid.version")
        with self.assertRaises(ValueError):
            TemplateVersion.parse("1.0")

    def test_column_definition_and_template_definition_serialization(self):
        col = ColumnDefinition("amount", "monto_bruto", "Decimal", required=True, default_value=Decimal("0.0"))
        col_dict = col.to_dict()
        self.assertEqual(col_dict["name"], "amount")
        self.assertEqual(col_dict["data_type"], "Decimal")
        self.assertTrue(col_dict["required"])

        tdef = TemplateDefinition(
            code="test_col",
            name="Test Col",
            version=TemplateVersion(1, 0, 0),
            columns=[col],
            target_entity="Finance",
        )
        tdef_dict = tdef.to_dict()
        self.assertEqual(tdef_dict["code"], "test_col")
        self.assertEqual(len(tdef_dict["columns"]), 1)

    def test_pipeline_definition_and_context_immutability(self):
        ctx = TemplateContext(tenant_id="t1", template_code="abc", parameters={"batch": 500})
        self.assertEqual(ctx.get_parameter("batch"), 500)
        self.assertEqual(ctx.get_parameter("missing", "default"), "default")
        with self.assertRaises(Exception):
            ctx.tenant_id = "t2"  # Frozen

        pipe_def = ImportPipelineDefinition(
            connector=ConnectorDefinition("csv", {"delimiter": ";"}),
            mapping={"col_a": "a"},
        )
        pdict = pipe_def.to_dict()
        self.assertEqual(pdict["connector"]["connector_type"], "csv")
        self.assertEqual(pdict["connector"]["parameters"]["delimiter"], ";")

    def test_template_validation_error_serialization(self):
        err = TemplateValidationError(code="ERR_1", message="Missing col", template_code="t_xyz", field="col_1")
        self.assertEqual(err.to_dict()["code"], "ERR_1")
        self.assertEqual(err.to_dict()["field"], "col_1")


# ==============================================================================
# 2. TemplateRegistry Tests
# ==============================================================================

class TestTemplateRegistry(unittest.TestCase):
    """Verify versioned registration, active version resolution, and multi-thread safety."""

    def setUp(self):
        self.registry = TemplateRegistry.global_registry()
        # Clean up any test artifacts before each test
        try:
            self.registry.remove("dummy_reg")
        except TemplateNotFoundException:
            pass

    def test_register_and_get_by_code_and_version(self):
        t1 = DummyTemplate("dummy_reg", "1.0.0")
        self.registry.register(t1, set_active=True)

        fetched = self.registry.get("dummy_reg", "1.0.0")
        self.assertEqual(fetched.code, "dummy_reg")
        self.assertEqual(str(fetched.version), "1.0.0")

        # Get active version directly without specifying version string
        fetched_active = self.registry.get("dummy_reg")
        self.assertEqual(str(fetched_active.version), "1.0.0")

    def test_version_conflict_without_overwrite_raises(self):
        t1 = DummyTemplate("dummy_reg", "1.0.0")
        self.registry.register(t1)
        with self.assertRaises(VersionConflictException):
            self.registry.register(t1, overwrite=False)

    def test_multiple_versions_and_set_active_version(self):
        t1 = DummyTemplate("dummy_reg", "1.0.0")
        t2 = DummyTemplate("dummy_reg", "1.1.0")
        t3 = DummyTemplate("dummy_reg", "2.0.0")

        self.registry.register(t1, set_active=True, overwrite=True)
        self.registry.register(t2, set_active=False, overwrite=True)
        self.registry.register(t3, set_active=False, overwrite=True)

        self.assertEqual(self.registry.get_active_version("dummy_reg"), "1.0.0")
        self.registry.set_active_version("dummy_reg", "2.0.0")
        self.assertEqual(self.registry.get_active_version("dummy_reg"), "2.0.0")
        self.assertEqual(str(self.registry.get("dummy_reg").version), "2.0.0")

    def test_get_unregistered_raises_not_found(self):
        with self.assertRaises(TemplateNotFoundException):
            self.registry.get("non_existent_code_12345")

    def test_list_templates_with_and_without_status_filter(self):
        ta = DummyTemplate("dummy_status", "1.0.0", status="ACTIVE")
        tb = DummyTemplate("dummy_status", "1.1.0", status="DEPRECATED")
        self.registry.register(ta, overwrite=True)
        self.registry.register(tb, overwrite=True)

        active_list = self.registry.list_templates(status="ACTIVE")
        depr_list = self.registry.list_templates(status="DEPRECATED")
        self.assertTrue(any(t.code == "dummy_status" and str(t.version) == "1.0.0" for t in active_list))
        self.assertTrue(any(t.code == "dummy_status" and str(t.version) == "1.1.0" for t in depr_list))
        self.registry.remove("dummy_status")

    def test_remove_specific_version_promotes_remaining(self):
        t1 = DummyTemplate("dummy_rem", "1.0.0")
        t2 = DummyTemplate("dummy_rem", "1.5.0")
        self.registry.register(t1, set_active=True, overwrite=True)
        self.registry.register(t2, set_active=False, overwrite=True)

        self.assertEqual(self.registry.get_active_version("dummy_rem"), "1.0.0")
        self.registry.remove("dummy_rem", "1.0.0")
        # Should automatically promote remaining version 1.5.0
        self.assertEqual(self.registry.get_active_version("dummy_rem"), "1.5.0")
        self.registry.remove("dummy_rem")

    def test_concurrent_registry_access(self):
        errors: List[Exception] = []

        def worker(idx: int):
            try:
                code = f"thread_tpl_{idx}"
                tpl = DummyTemplate(code, "1.0.0")
                self.registry.register(tpl, set_active=True, overwrite=True)
                fetched = self.registry.get(code)
                self.assertEqual(fetched.code, code)
                self.registry.remove(code)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(25)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)


# ==============================================================================
# 3. TemplatePipelineBuilder Tests
# ==============================================================================

class TestTemplatePipelineBuilder(unittest.TestCase):
    """Verify dynamic instantiation of connectors and transformation pipelines."""

    def test_build_connector_from_template(self):
        tpl = StudentEnrollmentTemplate()
        connector = TemplatePipelineBuilder.build_connector(tpl, source_params={"filepath": "/tmp/test.csv"})
        self.assertIsInstance(connector, BaseConnector)
        self.assertEqual(connector.config.connector_type, "csv")

    def test_build_connector_raises_for_unregistered_type(self):
        class BadConnTemplate(DummyTemplate):
            def get_pipeline_definition(self) -> ImportPipelineDefinition:
                return ImportPipelineDefinition(
                    connector=ConnectorDefinition("unregistered_conn_xyz", {}),
                )
        tpl = BadConnTemplate("bad_conn")
        with self.assertRaises(TemplateBuildException):
            TemplatePipelineBuilder.build_connector(tpl)

    def test_build_transformation_pipeline_from_template(self):
        tpl = StudentEnrollmentTemplate()
        pipeline = TemplatePipelineBuilder.build_transformation_pipeline(tpl)
        self.assertIsInstance(pipeline, TransformationPipeline)
        # Should have transformations (trim, rename_fields, type_cast) + validators (required, unique, regex)
        self.assertGreaterEqual(len(pipeline.transformations), 5)

    def test_build_transformation_pipeline_raises_for_unregistered_processor(self):
        class BadTxTemplate(DummyTemplate):
            def get_pipeline_definition(self) -> ImportPipelineDefinition:
                return ImportPipelineDefinition(
                    connector=ConnectorDefinition("csv", {}),
                    transformations=[TransformationDefinition("unregistered_processor_123", {})],
                )
        tpl = BadTxTemplate("bad_tx")
        with self.assertRaises(TemplateBuildException):
            TemplatePipelineBuilder.build_transformation_pipeline(tpl)

    def test_validate_execution_readiness_returns_true_for_valid_template(self):
        tpl = StudentEnrollmentTemplate()
        ready = TemplatePipelineBuilder.validate_execution_readiness(tpl)
        self.assertTrue(ready)

    def test_validate_execution_readiness_returns_false_for_invalid_template(self):
        class EmptyColTemplate(DummyTemplate):
            def get_template_definition(self) -> TemplateDefinition:
                return TemplateDefinition("empty_col", "Empty", TemplateVersion(1, 0, 0), columns=[])
        tpl = EmptyColTemplate("empty_col")
        self.assertFalse(TemplatePipelineBuilder.validate_execution_readiness(tpl))


# ==============================================================================
# 4. Standard Enterprise Templates Tests
# ==============================================================================

class TestStandardImportTemplates(unittest.TestCase):
    """Verify built-in templates (StudentEnrollmentTemplate, FinancialFeeTemplate)."""

    def test_student_enrollment_template_schema_and_execution(self):
        tpl = StudentEnrollmentTemplate()
        self.assertEqual(tpl.code, "student_enrollment")
        self.assertEqual(tpl.get_template_definition().target_entity, "Student")
        self.assertEqual(len(tpl.validate_template()), 0)
        self.assertTrue(tpl.can_handle({"entity": "Student"}))
        self.assertFalse(tpl.can_handle({"entity": "Teacher"}))

        # Build pipeline and process simulated data
        pipeline = TemplatePipelineBuilder.build_transformation_pipeline(tpl)
        records = [
            {
                "id_estudiante": "1001",
                "nombre_completo": "  Ana Perez  ",
                "correo": "ana.perez@eduka360.com",
                "fecha_matricula": "2026-07-12",
            },
            {
                "id_estudiante": "1001",  # Duplicate student ID -> REJECTED by UniqueValidator
                "nombre_completo": "Ana Perez Duplicada",
                "correo": "ana2@eduka360.com",
            },
            {
                "id_estudiante": "1002",
                "nombre_completo": "Juan Gomez",
                "correo": "invalid_email_format",  # Bad regex -> REJECTED by RegexValidator
            },
        ]
        report = pipeline.execute(records)
        self.assertEqual(report.statistics.records_processed, 3)
        self.assertEqual(report.statistics.records_accepted, 1)
        self.assertEqual(report.statistics.records_rejected, 2)
        # Verify accepted record structure and type casting
        clean_rec = report.results[0].transformed_record
        self.assertEqual(clean_rec["student_id"], 1001)
        self.assertEqual(clean_rec["full_name"], "Ana Perez")

    def test_financial_fee_template_schema_and_execution(self):
        tpl = FinancialFeeTemplate()
        self.assertEqual(tpl.code, "financial_fee")
        self.assertEqual(tpl.get_template_definition().target_entity, "Fee")
        self.assertEqual(len(tpl.validate_template()), 0)

        pipeline = TemplatePipelineBuilder.build_transformation_pipeline(tpl)
        records = [
            {
                "id_cuota": "5001",
                "id_estudiante": "1001",
                "monto": "150.75",
                "concepto": "  matricula periodo 2026  ",
            },
            {
                "id_cuota": "5002",
                "id_estudiante": "1001",
                "monto": "-50.00",  # Negative amount -> REJECTED by RangeValidator
                "concepto": "mora",
            },
        ]
        report = pipeline.execute(records)
        self.assertEqual(report.statistics.records_processed, 2)
        self.assertEqual(report.statistics.records_accepted, 1)
        self.assertEqual(report.statistics.records_rejected, 1)
        clean_rec = report.results[0].transformed_record
        self.assertEqual(clean_rec["fee_id"], 5001)
        self.assertEqual(clean_rec["amount"], Decimal("150.75"))
        self.assertEqual(clean_rec["concept"], "MATRICULA PERIODO 2026")


# ==============================================================================
# 5. Zero-ORM Compliance AST Inspection
# ==============================================================================

class TestZeroOrmComplianceInTemplates(unittest.TestCase):
    """Perform static AST verification to guarantee Zero-ORM in `templates/`."""

    def test_templates_package_has_no_django_orm_dependencies(self):
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
