# apps/data_engine/pipeline/tests/test_tarea31.py
"""Automated tests for TAREA 31: Pipeline Definition & Execution Framework."""

import ast
import os
import threading
import unittest
from typing import Any, Dict, List, Optional

from apps.data_engine.connectors.base import BaseConnector
from apps.data_engine.connectors.registry import ConnectorRegistry
from apps.data_engine.events.subscribers import CallbackEventSubscriber
from apps.data_engine.events.registry import EventBusRegistry
from apps.data_engine.progress.registry import ProgressRegistry
from apps.data_engine.progress.tracker import ProgressTracker
from apps.data_engine.templates.base import BaseImportTemplate
from apps.data_engine.templates.models import (
    ConnectorDefinition,
    ImportPipelineDefinition,
    TemplateDefinition,
    TemplateVersion,
)
from apps.data_engine.templates.packaging.manager import PackageManager
from apps.data_engine.templates.registry import TemplateRegistry
from apps.data_engine.transformations.base import BaseTransformation
from apps.data_engine.transformations.registry import TransformationRegistry
from apps.data_engine.quality.base import BaseQualityRule
from apps.data_engine.quality.models import QualityViolation
from apps.data_engine.quality.registry import QualityRuleRegistry
from apps.data_engine.rules.models import RuleCondition, RuleAction, BusinessRule, RuleViolation as BusinessViolation
from apps.data_engine.rules.registry import BusinessRuleRegistry

from apps.data_engine.pipeline import (
    PipelineDefinition,
    PipelineExecutionReport,
    PipelineRuntime,
    PipelineRuntimeRegistry,
    PipelineBuilder,
    PipelineExecutor,
    PipelineBuildError,
    PipelineExecutionError,
    PipelinePackageLoader,
)


class MockConnector(BaseConnector):
    """Mock connector returning static data."""

    component_type = "reader"

    def connect(self) -> None:
        self._is_connected = True

    def disconnect(self) -> None:
        self._is_connected = False

    def test_connection(self) -> bool:
        return True

    def fetch(self, query_or_path: Optional[str] = None, limit: Optional[int] = None, **kwargs: Any) -> List[Dict[str, Any]]:
        return [
            {"id": "1", "name": "Alice", "score": "95"},
            {"id": "2", "name": "Bob", "score": "80"},
            {"id": "3", "name": "Charlie", "score": "45"},
        ]

    def stream(self, query_or_path: Optional[str] = None, chunk_size: int = 1000, **kwargs: Any) -> Any:
        yield self.fetch()

    def metadata(self) -> Any:
        from apps.data_engine.connectors.datasource import DataSource
        return DataSource(name="mock_datasource", columns=[])


class MockTransformation(BaseTransformation):
    """Mock transformation for type casting score."""

    component_type = "transformation"

    @property
    def name(self) -> str:
        return "mock_tx"

    @property
    def description(self) -> str:
        return "Mock transformation"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return "score" in record

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        rec = dict(record)
        rec["score"] = int(rec["score"])
        return rec

    def validate(self, record: Dict[str, Any]) -> List[Any]:
        return []


class MockQualityRule(BaseQualityRule):
    """Mock quality rule rejecting low scores."""

    def __init__(self, code: str, field: str) -> None:
        self._code = code
        self._field = field

    @property
    def code(self) -> str:
        return self._code

    @property
    def field(self) -> Optional[str]:
        return self._field

    @property
    def severity(self) -> str:
        return "CRITICAL"

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        score = record.get("score")
        if score is not None and int(score) < 50:
            return [
                QualityViolation(
                    rule_code=self.code,
                    message="Score is too low",
                    field=self.field,
                    value=score,
                    severity=self.severity,
                )
            ]
        return []


class MockTemplate(BaseImportTemplate):
    """Mock template returning baseline definitions."""

    @property
    def code(self) -> str:
        return "mock_template"

    @property
    def name(self) -> str:
        return "Mock Template"

    @property
    def version(self) -> TemplateVersion:
        return TemplateVersion.parse("1.0.0")

    def get_template_definition(self) -> TemplateDefinition:
        return TemplateDefinition(
            code=self.code,
            name=self.name,
            version=self.version,
            columns=[],
            target_entity="Student",
        )

    def get_pipeline_definition(self) -> ImportPipelineDefinition:
        return ImportPipelineDefinition(
            connector=ConnectorDefinition(connector_type="mock_conn", parameters={}),
            transformations=[],
            validators=[],
        )

    def validate_template(self) -> List[Any]:
        return []


class TestPipelineDTOsAndRegistry(unittest.TestCase):
    """Verify DTO immutability, serialization and Runtime Registry thread-safety."""

    def test_pipeline_definition_dto(self) -> None:
        p_def = PipelineDefinition(
            pipeline_id="p-1",
            name="Test Pipeline",
            version="1.0.0",
            connector={"connector_type": "mock_conn"},
            template="mock_template",
            options={"opt": "val"},
        )
        self.assertEqual(p_def.pipeline_id, "p-1")
        self.assertEqual(p_def.template, "mock_template")
        self.assertEqual(p_def.options["opt"], "val")

        with self.assertRaises(Exception):
            p_def.pipeline_id = "p-2"  # frozen

        # Serialización roundtrip
        d = p_def.to_dict()
        self.assertEqual(d["pipeline_id"], "p-1")
        deser = PipelineDefinition.from_dict(d)
        self.assertEqual(deser.name, "Test Pipeline")

    def test_pipeline_execution_report_dto(self) -> None:
        report = PipelineExecutionReport(
            pipeline_id="p-1",
            run_id="run-123",
            start_time="2026-07-13T12:00:00Z",
            finish_time="2026-07-13T12:00:05Z",
            duration=5.0,
            processed=3,
            accepted=2,
            rejected=1,
            quality_score=95.0,
        )
        self.assertEqual(report.run_id, "run-123")
        self.assertEqual(report.quality_score, 95.0)

        with self.assertRaises(Exception):
            report.run_id = "run-456"

        d = report.to_dict()
        self.assertEqual(d["accepted"], 2)

    def test_runtime_registry_lifecycle(self) -> None:
        registry = PipelineRuntimeRegistry.global_registry()
        registry.clear()

        runtime = PipelineRuntime(
            connector=None,
            template=None,
            transformations=None,
            quality_engine=None,
            business_engine=None,
            workflow=None,
        )

        registry.register("run-1", runtime)
        self.assertEqual(registry.get("run-1"), runtime)

        registry.remove("run-1")
        with self.assertRaises(KeyError):
            registry.get("run-1")

    def test_runtime_registry_thread_safety(self) -> None:
        registry = PipelineRuntimeRegistry.global_registry()
        registry.clear()

        runtime = PipelineRuntime(
            connector=None,
            template=None,
            transformations=None,
            quality_engine=None,
            business_engine=None,
            workflow=None,
        )

        def worker(idx: int) -> None:
            registry.register(f"run-{idx}", runtime)
            registry.get(f"run-{idx}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for i in range(50):
            self.assertEqual(registry.get(f"run-{i}"), runtime)
        registry.clear()


class TestPipelineBuilderAndExecutor(unittest.TestCase):
    """Verify build resolution and executor workflow runs."""

    def setUp(self) -> None:
        TemplateRegistry.reset_global_registry()
        ConnectorRegistry.global_registry().register("mock_conn", MockConnector)
        TransformationRegistry.global_registry().register("mock_tx", MockTransformation)
        QualityRuleRegistry.global_registry().reset()
        BusinessRuleRegistry.global_registry().clear()

    def test_builder_instantiates_runtime_correctly(self) -> None:
        tpl = MockTemplate()
        TemplateRegistry.global_registry().register(tpl)

        # Register a mock quality rule
        q_rule = MockQualityRule(code="q_score", field="score")
        QualityRuleRegistry.global_registry().register(q_rule)

        # Register a mock business rule (requires score >= 80)
        cond = RuleCondition(field="score", operator="GREATER_OR_EQUAL", value=80)
        act = RuleAction(action_type="SET_VALUE", parameters={"field": "category", "value": "EXCELLENT"})
        b_rule = BusinessRule(rule_code="b_excellent", condition=cond, actions=[act])
        BusinessRuleRegistry.global_registry().register(b_rule)

        definition = PipelineDefinition(
            pipeline_id="p-test",
            name="Builder Test",
            version="1.0.0",
            connector={"connector_type": "mock_conn"},
            template="mock_template",
            transformations=[{"transformation_type": "mock_tx"}],
            quality_rules=[{"rule_code": "q_score"}],
            business_rules=[{"rule_code": "b_excellent"}],
        )

        builder = PipelineBuilder()
        runtime = builder.build(definition)

        self.assertIsNotNone(runtime.connector)
        self.assertEqual(runtime.template, tpl)
        self.assertIsNotNone(runtime.transformations)
        self.assertIsNotNone(runtime.quality_engine)
        self.assertIsNotNone(runtime.business_engine)
        self.assertIsNotNone(runtime.workflow)
        self.assertEqual(len(runtime.configuration["quality_rules"]), 1)
        self.assertEqual(len(runtime.configuration["business_rules"]), 1)

    def test_executor_execution_flow(self) -> None:
        tpl = MockTemplate()
        TemplateRegistry.global_registry().register(tpl)

        q_rule = MockQualityRule(code="q_score", field="score")
        QualityRuleRegistry.global_registry().register(q_rule)

        cond = RuleCondition(field="score", operator="GREATER_OR_EQUAL", value=80)
        act = RuleAction(action_type="SET_VALUE", parameters={"field": "category", "value": "EXCELLENT"})
        b_rule = BusinessRule(rule_code="b_excellent", condition=cond, actions=[act])
        BusinessRuleRegistry.global_registry().register(b_rule)

        definition = PipelineDefinition(
            pipeline_id="p-test",
            name="Executor Test",
            version="1.0.0",
            connector={"connector_type": "mock_conn"},
            template="mock_template",
            transformations=[{"transformation_type": "mock_tx"}],
            quality_rules=[{"rule_code": "q_score"}],
            business_rules=[{"rule_code": "b_excellent"}],
        )

        builder = PipelineBuilder()
        runtime = builder.build(definition)

        executor = PipelineExecutor()
        session_id = "test-session-999"

        # Capture events
        events_emitted = []
        def on_event(envelope: Any) -> None:
            if envelope.session_id == session_id:
                events_emitted.append(envelope.event_type)

        sub = CallbackEventSubscriber(on_event)
        EventBusRegistry.global_registry().get_dispatcher().subscribe(sub)

        # Run executor
        report = executor.execute(
            runtime=runtime,
            tenant_id="tenant-1",
            user_id="user-1",
            run_id=session_id,
            is_dry_run=True,
        )

        EventBusRegistry.global_registry().get_dispatcher().unsubscribe(sub)

        # Alice: score 95 -> passed quality -> business match >=80 -> category SET_VALUE -> ACCEPTED
        # Bob: score 80 -> passed quality -> business match >=80 -> category SET_VALUE -> ACCEPTED
        # Charlie: score 45 -> REJECTED by MockQualityRule (score < 50)
        self.assertEqual(report.processed, 3)
        self.assertEqual(report.accepted, 2)
        self.assertEqual(report.rejected, 1)

        # Event Bus events checked
        self.assertIn("PIPELINE_STARTED", events_emitted)
        self.assertIn("PIPELINE_COMPLETED", events_emitted)

        # Progress tracker checks
        tracker = ProgressRegistry.global_registry().get(session_id)
        self.assertIsNotNone(tracker)
        self.assertEqual(tracker._records_processed, 2)  # final stage updates

    def test_executor_failure_publishes_event(self) -> None:
        # Invalid connector type raises build error or execution error
        definition = PipelineDefinition(
            pipeline_id="p-fail",
            name="Fail Test",
            version="1.0.0",
            connector={"connector_type": "non_existent_type"},
        )

        builder = PipelineBuilder()
        with self.assertRaises(PipelineBuildError):
            builder.build(definition)


class TestPackageManagerAndPipelineCompatibility(unittest.TestCase):
    """Verify loading PipelineDefinition directly from signed packages."""

    def test_pack_and_unpack_pipeline_definition(self) -> None:
        tpl = MockTemplate()
        TemplateRegistry.reset_global_registry()
        TemplateRegistry.global_registry().register(tpl)

        pm = PackageManager()
        key = b"secret_key_for_pipeline_testing_32bytes"
        pkg_path = "temp_pipeline_package.macpkg"

        # Pack
        pm.pack(tpl, key, pkg_path, description="Declarative pipeline package")

        # Unpack pipeline directly
        p_def = PipelinePackageLoader.load(pkg_path, key)

        # Clean up
        if os.path.exists(pkg_path):
            os.remove(pkg_path)

        self.assertIsNotNone(p_def)
        self.assertEqual(p_def.pipeline_id, "mock_template")
        self.assertEqual(p_def.name, "Mock Template")
        self.assertEqual(p_def.version, "1.0.0")
        self.assertEqual(p_def.connector["connector_type"], "mock_conn")


# ==============================================================================
# AST Auditoria Compliance
# ==============================================================================

class TestZeroOrmComplianceInPipeline(unittest.TestCase):
    """Verify Zero-ORM compliance in the pipeline framework package."""

    def test_pipeline_package_has_no_django_orm_dependencies(self) -> None:
        forbidden_modules = {"django.db", "django.db.models", "django.db.transaction"}
        forbidden_names = {"models", "QuerySet", "atomic"}

        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for root, _, files in os.walk(package_dir):
            for file in files:
                if not file.endswith(".py") or "tests" in root:
                    continue
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=path)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            self.assertNotIn(
                                name.name,
                                forbidden_modules,
                                f"Forbidden import '{name.name}' in {file}",
                            )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self.assertNotIn(
                                node.module,
                                forbidden_modules,
                                f"Forbidden import from '{node.module}' in {file}",
                            )
                            for name in node.names:
                                self.assertNotIn(
                                    name.name,
                                    forbidden_names,
                                    f"Forbidden import name '{name.name}' from module '{node.module}' in {file}",
                                )
