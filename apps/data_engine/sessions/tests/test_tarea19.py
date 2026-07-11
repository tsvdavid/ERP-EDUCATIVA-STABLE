# apps/data_engine/sessions/tests/test_tarea19.py
"""Comprehensive automated tests for TAREA 19: Import Workflow Orchestrator & Session Management Framework.

Verifies:
1. Abstract contracts cannot be directly instantiated.
2. SessionTracker finite state machine transitions and monotonic timing metrics.
3. ImportWorkflowOrchestrator happy path across all 10 MAC pipeline phases.
4. Abort cascades when validation or graph planning fails (stopping downstream execution).
5. Integration with TAREA 18 (DjangoOrmStepExecutor) for actual multi-tenant ORM persistence.
"""

import os
import sys
import sqlite3
import pytest
from unittest.mock import MagicMock

workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
backend_dir = os.path.join(workspace_root, "backend")
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.db.backends.sqlite3.base import SQLiteCursorWrapper
_orig_sqlite_execute = SQLiteCursorWrapper.execute

def _safe_sqlite_execute(self, query, params=None):
    if isinstance(query, str) and query.strip().upper().startswith(("SET LOCAL", "RESET")):
        return None
    return _orig_sqlite_execute(self, query, params)

SQLiteCursorWrapper.execute = _safe_sqlite_execute

from django.db import connection

from apps.data_engine.components.base import BaseComponent, MacContext
from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.components.loaders.models import LoadNode, LoadPlan
from apps.data_engine.persistence import DjangoOrmStepExecutor
from apps.data_engine.sessions import (
    BaseSessionTracker,
    BaseWorkflowOrchestrator,
    ImportSession,
    ImportWorkflowOrchestrator,
    InvalidSessionStateTransitionError,
    PhaseResult,
    SessionReport,
    SessionState,
    SessionTracker,
)
from users.models import Institution
from academic.models import Course


# --- Dummy Components for Testing the 10-Layer Pipeline ---

class DummyReaderComponent(BaseComponent):
    def execute(self, context: MacContext) -> MacContext:
        context["payload"]["raw_data"] = ["codigo,nombre", "INST01,Universidad Test"]
        return context


class DummyParserComponent(BaseComponent):
    def execute(self, context: MacContext) -> MacContext:
        raw = context["payload"].get("raw_data", [])
        context["payload"]["parsed_records"] = [
            {"codigo": "INST01", "nombre": "Universidad Test"}
        ]
        return context


class DummyValidatorComponent(BaseComponent):
    def execute(self, context: MacContext) -> MacContext:
        if context["metadata"].get("force_validation_error"):
            raise ValueError("Required field 'nombre' is missing or invalid")
        context["payload"]["validated_records"] = context["payload"].get("parsed_records", [])
        return context


class DummyMapperComponent(BaseComponent):
    def execute(self, context: MacContext) -> MacContext:
        context["payload"]["mapped_records"] = [
            {"code": "INST01", "name": "Universidad Test"}
        ]
        return context


class DummyCasterComponent(BaseComponent):
    def execute(self, context: MacContext) -> MacContext:
        context["payload"]["staged_records"] = context["payload"].get("mapped_records", [])
        return context


class DummyStagingComponent(BaseComponent):
    def execute(self, context: MacContext) -> MacContext:
        context["payload"]["staged_batch_id"] = "batch_123"
        return context


class DummyReconciliationComponent(BaseComponent):
    def execute(self, context: MacContext) -> MacContext:
        manifest = MagicMock()
        manifest.status = "BALANCED"
        context["reconciliation_manifest"] = manifest
        return context


class DummyLoaderPlannerComponent(BaseComponent):
    def execute(self, context: MacContext) -> MacContext:
        if context["metadata"].get("force_cyclic_error"):
            plan = LoadPlan(
                plan_id="plan_cyclic",
                execution_groups=[],
                ordered_nodes=[],
                has_cycles=True,
            )
            context["load_plan"] = plan
            return context

        node = LoadNode(node_id="inst_1", entity_name="Institution")
        plan = LoadPlan(
            plan_id="plan_happy",
            execution_groups=[[node]],
            ordered_nodes=[node],
            has_cycles=False,
        )
        context["load_plan"] = plan
        return context


class DummyExecutionEngineComponent(BaseComponent):
    def execute(self, context: MacContext) -> MacContext:
        exec_result = MagicMock()
        exec_result.failed_steps = 0
        exec_result.successful_steps = 1
        context["execution_result"] = exec_result
        return context


# --- Tests ---

class TestSessionAbstractContracts:
    """Verifies that BaseSessionTracker and BaseWorkflowOrchestrator cannot be instantiated."""

    def test_abstract_contracts_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            BaseSessionTracker()
        with pytest.raises(TypeError):
            BaseWorkflowOrchestrator()


class TestSessionTrackerStateMachine:
    """Verifies finite state transitions, rejection of illegal jumps, and phase metrics timing."""

    def test_valid_state_transitions(self):
        session = ImportSession("sess_1", "t_1", "u_1", "run_1")
        tracker = SessionTracker(session)

        assert tracker.session.state == SessionState.CREATED
        tracker.transition_to(SessionState.INGESTING)
        assert tracker.session.state == SessionState.INGESTING
        tracker.transition_to(SessionState.PARSING)
        assert tracker.session.state == SessionState.PARSING
        tracker.transition_to(SessionState.VALIDATING)
        assert tracker.session.state == SessionState.VALIDATING

    def test_invalid_state_transitions_raise_error(self):
        session = ImportSession("sess_2", "t_1", "u_1", "run_1")
        tracker = SessionTracker(session)

        # Illegal jump from CREATED directly to PERSISTING
        with pytest.raises(InvalidSessionStateTransitionError):
            tracker.transition_to(SessionState.PERSISTING)

        # Illegal jump backward from COMPLETED to INGESTING
        tracker._session.state = SessionState.COMPLETED
        with pytest.raises(InvalidSessionStateTransitionError):
            tracker.transition_to(SessionState.INGESTING)

    def test_start_and_end_phase_timing_and_metrics(self):
        session = ImportSession("sess_3", "t_1", "u_1", "run_1")
        tracker = SessionTracker(session)

        start_t = tracker.start_phase("TestPhase", SessionState.INGESTING)
        assert tracker.session.state == SessionState.INGESTING

        res = tracker.end_phase(
            phase_name="TestPhase",
            start_time=start_t,
            success=True,
            input_count=100,
            output_count=98,
            metadata={"source": "file.csv"},
        )
        assert isinstance(res, PhaseResult)
        assert res.success is True
        assert res.input_record_count == 100
        assert res.output_record_count == 98
        assert res.duration_ms >= 0.0
        assert "TestPhase" in tracker.session.phases
        assert tracker.session.total_duration_ms >= 0.0

    def test_abort_session_records_reason(self):
        session = ImportSession("sess_4", "t_1", "u_1", "run_1")
        tracker = SessionTracker(session)
        tracker.transition_to(SessionState.INGESTING)

        tracker.abort_session("Critical syntax error", SessionState.FAILED)
        assert tracker.session.state == SessionState.FAILED
        assert tracker.session.error_message == "Critical syntax error"


class TestImportWorkflowOrchestratorHappyPath:
    """Verifies the 10-layer sequential orchestration using registered MAC components."""

    @pytest.fixture
    def registry_with_components(self):
        reg = MacRegistry()
        reg.register("t19_reader", DummyReaderComponent())
        reg.register("t19_parser", DummyParserComponent())
        reg.register("t19_validator", DummyValidatorComponent())
        reg.register("t19_mapper", DummyMapperComponent())
        reg.register("t19_caster", DummyCasterComponent())
        reg.register("t19_staging", DummyStagingComponent())
        reg.register("t19_reconcile", DummyReconciliationComponent())
        reg.register("t19_planner", DummyLoaderPlannerComponent())
        reg.register("t19_execution", DummyExecutionEngineComponent())
        return reg

    def test_run_workflow_happy_path(self, registry_with_components):
        orchestrator = ImportWorkflowOrchestrator(registry=registry_with_components)
        pipeline_config = {
            "reader": "t19_reader",
            "parser": "t19_parser",
            "validators": ["t19_validator"],
            "mapper": "t19_mapper",
            "casters": ["t19_caster"],
            "staging": "t19_staging",
            "reconciliation": "t19_reconcile",
            "loader": "t19_planner",
            "execution_engine": "t19_execution",
        }

        report = orchestrator.run_workflow(
            tenant_id="inst_001",
            user_id="user_admin",
            source="test_data.csv",
            pipeline_config=pipeline_config,
            is_dry_run=True,
        )
        assert isinstance(report, SessionReport)
        assert report.final_state == SessionState.COMPLETED
        assert report.successful_phases == 10
        assert report.failed_phases == 0
        assert report.error_summary is None


class TestImportWorkflowAbortCascades:
    """Verifies immediate abort behavior and downstream phase skipping on failures."""

    @pytest.fixture
    def registry_with_components(self):
        reg = MacRegistry()
        reg.register("t19_reader", DummyReaderComponent())
        reg.register("t19_parser", DummyParserComponent())
        reg.register("t19_validator", DummyValidatorComponent())
        reg.register("t19_planner", DummyLoaderPlannerComponent())
        return reg

    def test_abort_on_validation_error(self, registry_with_components):
        orchestrator = ImportWorkflowOrchestrator(registry=registry_with_components)
        pipeline_config = {
            "reader": "t19_reader",
            "parser": "t19_parser",
            "validators": ["t19_validator"],
            "loader": "t19_planner",
        }

        # Passing force_validation_error in metadata/source or modifying orchestrator run
        # We can pass metadata directly or mock the validator behavior
        DummyValidatorComponent.execute = MagicMock(side_effect=ValueError("Mandatory field missing"))

        report = orchestrator.run_workflow(
            tenant_id="inst_002",
            user_id="user_admin",
            source="bad_data.csv",
            pipeline_config=pipeline_config,
        )
        assert report.final_state == SessionState.FAILED
        assert report.failed_phases == 1
        assert "Mandatory field missing" in str(report.error_summary)
        # Verify planner and downstream phases were NEVER run
        phase_names = [p.phase_name for p in report.phase_results]
        assert "Loader Planning" not in phase_names
        assert "Execution Engine" not in phase_names

    def test_abort_on_cyclic_dependency_in_planner(self, registry_with_components):
        # Restore validator component
        DummyValidatorComponent.execute = lambda self, ctx: ctx

        orchestrator = ImportWorkflowOrchestrator(registry=registry_with_components)
        pipeline_config = {
            "reader": "t19_reader",
            "parser": "t19_parser",
            "validators": ["t19_validator"],
            "loader": "t19_planner",
        }

        # Force cyclic error in planner component via execute override
        def _cyclic_execute(self, ctx):
            plan = LoadPlan(plan_id="cyclic", execution_groups=[], ordered_nodes=[], has_cycles=True)
            ctx["load_plan"] = plan
            return ctx
        DummyLoaderPlannerComponent.execute = _cyclic_execute

        report = orchestrator.run_workflow(
            tenant_id="inst_003",
            user_id="user_admin",
            source="cyclic_data.csv",
            pipeline_config=pipeline_config,
        )
        assert report.final_state == SessionState.FAILED
        assert "Cyclic dependency detected" in str(report.error_summary)
        phase_names = [p.phase_name for p in report.phase_results]
        assert "Execution Engine" not in phase_names
        assert "Persistence Adapter" not in phase_names


@pytest.mark.django_db(transaction=True)
class TestImportWorkflowPersistenceIntegration:
    """Verifies actual database persistence across the 10 layers with DjangoOrmStepExecutor (TAREA 18)."""

    def _clean_db_fixtures(self):
        from django.core.management import call_command
        call_command("migrate", run_syncdb=True, interactive=False, verbosity=0)
        with connection.cursor() as cursor:
            if connection.vendor == "sqlite":
                cursor.execute("PRAGMA foreign_keys = OFF;")
                existing_tables = set(connection.introspection.table_names(cursor))
                for table in [
                    "subscriptions_subscription",
                    "notifications_emailconfig",
                    "notifications_emailtemplate",
                    "core_actionlog",
                    "academic_enrollment",
                    "academic_course",
                    "academic_academicperiod",
                    "users_user",
                    "users_institution",
                ]:
                    if table in existing_tables:
                        cursor.execute(f'DELETE FROM "{table}";')
                cursor.execute("PRAGMA foreign_keys = ON;")

    def _intercept_sqlite_rls(self):
        original_execute = connection.cursor().cursor.execute
        if getattr(connection.cursor().cursor, "_intercepted", False):
            return
        def wrapper(sql, params=None):
            if isinstance(sql, str) and ("SET LOCAL app.current_tenant" in sql or "RESET app.current_tenant" in sql):
                return
            return original_execute(sql, params or ())
        connection.cursor().cursor.execute = wrapper
        connection.cursor().cursor._intercepted = True

    def test_run_workflow_persists_to_django_orm(self):
        self._clean_db_fixtures()
        if connection.vendor == "sqlite":
            self._intercept_sqlite_rls()

        reg = MacRegistry()
        reg.register("t19_reader", DummyReaderComponent())
        reg.register("t19_parser", DummyParserComponent())

        # Custom planner creating two sequential LoadNodes: Institution -> Course
        class RealOrmPlanner(BaseComponent):
            def execute(self, context: MacContext) -> MacContext:
                n1 = LoadNode(
                    node_id="n_inst",
                    entity_name="Institution",
                    payload_reference={"name": "Colegio T19", "ruc": "0912345678001", "is_active": True},
                )
                n2 = LoadNode(
                    node_id="n_course",
                    entity_name="Course",
                    payload_reference={"name": "Física T19", "level": "BACHILLERATO", "year": 2026, "parallel": "A"},
                    dependencies={"n_inst"},
                )
                plan = LoadPlan(
                    plan_id="plan_orm_t19",
                    execution_groups=[[n1], [n2]],
                    ordered_nodes=[n1, n2],
                    has_cycles=False,
                )
                context["load_plan"] = plan
                return context

        reg.register("t19_real_planner", RealOrmPlanner())

        step_executor = DjangoOrmStepExecutor()
        orchestrator = ImportWorkflowOrchestrator(
            step_executor=step_executor,
            registry=reg,
        )

        pipeline_config = {
            "reader": "t19_reader",
            "parser": "t19_parser",
            "loader": "t19_real_planner",
        }

        report = orchestrator.run_workflow(
            tenant_id="default",
            user_id="admin_t19",
            source="dummy_source.csv",
            pipeline_config=pipeline_config,
            is_dry_run=False,
        )

        assert report.final_state == SessionState.COMPLETED, f"Error: {report.error_summary} | Phases: {[p.phase_name + ':' + str(p.success) + ':' + str(p.errors) for p in report.phase_results]}"
        assert report.successful_phases == report.total_phases_executed
        assert report.failed_phases == 0

        # Verify exact DB state via ORM query
        db_inst = Institution.objects.filter(ruc="0912345678001").first()
        assert db_inst is not None
        assert db_inst.name == "Colegio T19"

        db_course = Course.objects.unscoped().filter(name="Física T19", year=2026).first()
        assert db_course is not None
        assert db_course.institution_id == db_inst.id
