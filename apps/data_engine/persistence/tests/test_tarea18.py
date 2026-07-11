# apps/data_engine/persistence/tests/test_tarea18.py
"""Automated unit and integration tests for TAREA 18 (MAC): Transactional Persistence Adapter.

Covers:
- Abstract contracts and non-instantiability (`BaseRepository`, `BasePersistenceExecutor`).
- Domain entities (`EntityPersistenceResult`, `TransactionResult`, `PersistenceContext`).
- Centralized registry and resolver (`RepositoryRegistry`, `RepositoryResolver`).
- Atomic ORM step execution (`DjangoOrmStepExecutor`) with savepoints and rollback (`django_db`).
- Idempotent entity update (`find_existing` -> `update`).
- Exception handling and savepoint rollback (`IntegrityError`, `ValidationError`).
- Integration with `SequentialExecutionStrategy` across multi-tenant graph nodes.
"""

import os
import sys
import unittest
import pytest

# Initialize Django environment and test database before importing ORM models
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

# Make SQLite cursor tolerate PostgreSQL RLS commands (SET LOCAL / RESET) during unit tests
from django.db.backends.sqlite3.base import SQLiteCursorWrapper
_orig_sqlite_execute = SQLiteCursorWrapper.execute

def _safe_sqlite_execute(self, query, params=None):
    if isinstance(query, str) and query.strip().upper().startswith(("SET LOCAL", "RESET")):
        return None
    return _orig_sqlite_execute(self, query, params)

SQLiteCursorWrapper.execute = _safe_sqlite_execute

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction

from apps.data_engine.components.execution.models import (
    ExecutionContext,
    ExecutionReport,
    ExecutionResult,
    ExecutionState,
    ExecutionStep,
)
from apps.data_engine.components.execution.strategies import SequentialExecutionStrategy
from apps.data_engine.components.loaders.models import LoadNode, LoadPlan
from apps.data_engine.persistence.adapters import RepositoryResolver
from apps.data_engine.persistence.base import BasePersistenceExecutor, BaseRepository
from apps.data_engine.persistence.executor import DjangoOrmStepExecutor
from apps.data_engine.persistence.models import (
    EntityPersistenceResult,
    PersistenceContext,
    TransactionResult,
)
from apps.data_engine.persistence.registry import RepositoryRegistry
from apps.data_engine.persistence.repositories import (
    CourseRepository,
    InstitutionRepository,
    StudentRepository,
)


def clean_db_fixtures():
    """Clean all test fixtures cleanly ignoring SQLite FK constraints and bypassing TenantManager filters."""
    from academic.models import Course
    from core.models import ActionLog
    from notifications.models import EmailConfig, EmailTemplate
    from subscriptions.models import Subscription
    from users.models import Institution

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF;")
        for table in [
            Course._meta.db_table,
            ActionLog._meta.db_table,
            Subscription._meta.db_table,
            EmailConfig._meta.db_table,
            EmailTemplate._meta.db_table,
            Institution._meta.db_table,
        ]:
            cursor.execute(f'DELETE FROM "{table}";')
        cursor.execute("PRAGMA foreign_keys = ON;")


class TestPersistenceModelsContracts(unittest.TestCase):
    """Test abstract contracts and transactional domain entities."""

    def test_abstract_contracts_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            BaseRepository()
        with self.assertRaises(TypeError):
            BasePersistenceExecutor()

    def test_domain_entities_defaults(self):
        res = EntityPersistenceResult(node_id="node_1", entity_name="Institution")
        self.assertEqual(res.node_id, "node_1")
        self.assertEqual(res.entity_name, "Institution")
        self.assertFalse(res.created)
        self.assertTrue(res.success)
        self.assertIsInstance(res.timestamp, str)

        tx_res = TransactionResult(success=True, entity_result=res)
        self.assertTrue(tx_res.success)
        self.assertEqual(tx_res.entity_result, res)

        ctx = PersistenceContext(tenant_id="inst_101")
        self.assertEqual(ctx.tenant_id, "inst_101")
        self.assertFalse(ctx.is_dry_run)
        self.assertEqual(ctx.resolved_dependencies, {})


class TestRepositoryRegistryAndResolver(unittest.TestCase):
    """Test repository registry and node resolution."""

    def setUp(self):
        from apps.data_engine.persistence import register_builtin_repositories
        register_builtin_repositories()

    def test_builtin_repositories_registered(self):
        entities = RepositoryRegistry.all_entities()
        self.assertIn("Institution", entities)
        self.assertIn("Course", entities)
        self.assertIn("Student", entities)
        self.assertIn("Representative", entities)
        self.assertIn("AcademicPeriod", entities)
        self.assertIn("Enrollment", entities)

    def test_registry_get_and_resolver(self):
        repo = RepositoryRegistry.get("Institution")
        self.assertIsInstance(repo, InstitutionRepository)

        node = LoadNode(node_id="course_1", entity_name="Course")
        resolved = RepositoryResolver.resolve_for_node(node)
        self.assertIsInstance(resolved, CourseRepository)

    def test_resolve_invalid_or_missing_raises_error(self):
        with self.assertRaises(KeyError):
            RepositoryResolver.resolve("NonExistentEntity")

        with self.assertRaises(TypeError):
            RepositoryResolver.resolve_for_node(object())

    def test_register_invalid_type_raises_type_error(self):
        class InvalidRepo:
            pass

        with self.assertRaises(TypeError):
            RepositoryRegistry.register(InvalidRepo)


class TestOrmStepExecutorExecution(unittest.TestCase):
    """Test DjangoOrmStepExecutor with database persistence and savepoint rollback."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("migrate", run_syncdb=True, interactive=False, verbosity=0)
        from apps.data_engine.persistence import register_builtin_repositories
        register_builtin_repositories()

    def setUp(self):
        clean_db_fixtures()

    def tearDown(self):
        clean_db_fixtures()

    def test_execute_step_create_institution_success(self):
        from users.models import Institution
        executor = DjangoOrmStepExecutor()
        node = LoadNode(
            node_id="inst_step_1",
            entity_name="Institution",
            payload_reference={
                "name": "Colegio Prisca E2E",
                "ruc": "1790010020001",
                "email": "info@prisca.edu.ec",
            },
        )
        step = ExecutionStep(step_id="step_inst_1", node=node)
        plan = LoadPlan(plan_id="plan_inst", execution_groups=[[node]])
        exec_ctx = ExecutionContext(plan=plan, shared_state={"institution_id": "default"})

        res = executor.execute_step(step, exec_ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.state, ExecutionState.COMPLETED)
        self.assertIn("orm_id", res.output_data)

        # Verify DB insertion
        db_inst = Institution.objects.filter(ruc="1790010020001").first()
        self.assertIsNotNone(db_inst)
        self.assertEqual(db_inst.name, "Colegio Prisca E2E")

    def test_execute_step_idempotent_update(self):
        from users.models import Institution
        executor = DjangoOrmStepExecutor()
        # Pre-create institution
        existing_inst = Institution.objects.create(
            name="Old Name", ruc="1799998887771"
        )

        node = LoadNode(
            node_id="inst_step_up",
            entity_name="Institution",
            payload_reference={
                "name": "Updated Institution Name",
                "ruc": "1799998887771",
            },
        )
        step = ExecutionStep(step_id="step_inst_up", node=node)
        plan = LoadPlan(plan_id="plan_up", execution_groups=[[node]])
        exec_ctx = ExecutionContext(plan=plan, shared_state={"institution_id": "default"})

        res = executor.execute_step(step, exec_ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.state, ExecutionState.COMPLETED)

        # Verify record updated without duplicate insertion
        self.assertEqual(Institution.objects.filter(ruc="1799998887771").count(), 1)
        existing_inst.refresh_from_db()
        self.assertEqual(existing_inst.name, "Updated Institution Name")
        self.assertFalse(res.output_data["entity_result"].created)

    def test_execute_step_validation_error_triggers_savepoint_rollback(self):
        from users.models import Institution
        executor = DjangoOrmStepExecutor()
        initial_count = Institution.objects.count()

        # Missing required 'name' -> triggers ValidationError
        node = LoadNode(
            node_id="inst_err",
            entity_name="Institution",
            payload_reference={"ruc": "1234567890001"},
        )
        step = ExecutionStep(step_id="step_err", node=node)
        plan = LoadPlan(plan_id="plan_err", execution_groups=[[node]])
        exec_ctx = ExecutionContext(plan=plan, shared_state={"institution_id": "default"})

        res = executor.execute_step(step, exec_ctx)
        self.assertFalse(res.success)
        self.assertEqual(res.state, ExecutionState.FAILED)
        self.assertIn("ValidationError", res.error)

        # Verify zero DB mutation
        self.assertEqual(Institution.objects.count(), initial_count)

    def test_execute_step_simulate_error_flag(self):
        executor = DjangoOrmStepExecutor()
        node = LoadNode(
            node_id="inst_sim",
            entity_name="Institution",
            payload_reference={"name": "Simulated School", "simulate_error": True},
        )
        step = ExecutionStep(step_id="step_sim", node=node)
        plan = LoadPlan(plan_id="plan_sim", execution_groups=[[node]])
        exec_ctx = ExecutionContext(plan=plan, shared_state={"institution_id": "default"})

        res = executor.execute_step(step, exec_ctx)
        self.assertFalse(res.success)
        self.assertEqual(res.state, ExecutionState.FAILED)
        self.assertIn("SimulatedError", res.error)

    def test_execute_step_dry_run_rollback(self):
        from users.models import Institution
        executor = DjangoOrmStepExecutor()
        initial_count = Institution.objects.count()

        node = LoadNode(
            node_id="inst_dry",
            entity_name="Institution",
            payload_reference={"name": "Dry Run College", "ruc": "1112223334441"},
        )
        step = ExecutionStep(step_id="step_dry", node=node)
        plan = LoadPlan(plan_id="plan_dry", execution_groups=[[node]])
        exec_ctx = ExecutionContext(
            plan=plan,
            shared_state={"institution_id": "default", "is_dry_run": True},
        )

        res = executor.execute_step(step, exec_ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.state, ExecutionState.COMPLETED)

        # Verify zero records committed due to dry_run rollback
        self.assertEqual(Institution.objects.count(), initial_count)


class TestExecutionEngineAndPersistenceIntegration(unittest.TestCase):
    """Test full integration of SequentialExecutionStrategy with DjangoOrmStepExecutor across multiple dependent nodes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("migrate", run_syncdb=True, interactive=False, verbosity=0)
        from apps.data_engine.persistence import register_builtin_repositories
        register_builtin_repositories()

    def setUp(self):
        clean_db_fixtures()

    def tearDown(self):
        clean_db_fixtures()

    def test_sequential_strategy_persists_dependent_graph_cleanly(self):
        from academic.models import Course
        from users.models import Institution

        executor = DjangoOrmStepExecutor()
        strategy = SequentialExecutionStrategy()

        # Node 1: Institution
        inst_node = LoadNode(
            node_id="node_inst_A",
            entity_name="Institution",
            payload_reference={"name": "Universidad MAC 101", "ruc": "0987654321001"},
        )
        # Node 2: Course dependent on Institution
        course_node = LoadNode(
            node_id="node_course_A",
            entity_name="Course",
            payload_reference={
                "name": "Matemáticas Avanzadas",
                "year": 2026,
                "parallel": "X",
                "level": "Superior",
            },
            dependencies={"node_inst_A"},
        )

        plan = LoadPlan(
            plan_id="plan_graph_e2e",
            ordered_nodes=[inst_node, course_node],
            execution_groups=[[inst_node], [course_node]],
        )

        exec_ctx = ExecutionContext(plan=plan, shared_state={"institution_id": "default"})
        report = strategy.execute_plan(exec_ctx, executor)

        self.assertEqual(report.status, ExecutionState.COMPLETED)
        self.assertEqual(report.metrics.total_steps, 2)
        self.assertEqual(report.metrics.completed_steps, 2)
        self.assertEqual(report.metrics.failed_steps, 0)

        # Verify DB state
        db_inst = Institution.objects.filter(ruc="0987654321001").first()
        self.assertIsNotNone(db_inst)

        db_course = Course.objects.unscoped().filter(name="Matemáticas Avanzadas", year=2026).first()
        self.assertIsNotNone(db_course)
        # Check FK relation resolved via context
        self.assertEqual(db_course.institution_id, db_inst.id)


if __name__ == "__main__":
    unittest.main()
