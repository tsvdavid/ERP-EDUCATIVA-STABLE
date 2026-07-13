# apps/data_engine/integration/tests/test_tarea32.py
"""Automated tests for TAREA 32 ERP Integration Layer & Persistence Gateway."""

import ast
import os
import threading
import unittest
from dataclasses import FrozenInstanceError
from typing import Any, Dict, List, Optional

from apps.data_engine.events.models import EventCategory, EventEnvelope
from apps.data_engine.events.registry import EventBusRegistry
from apps.data_engine.progress.tracker import ProgressTracker
from apps.data_engine.progress.registry import ProgressRegistry

from apps.data_engine.integration import (
    AdapterNotFoundError,
    BatchPersistenceResult,
    EntityMapping,
    InMemoryTransactionManager,
    IntegrationRegistry,
    MacIntegrationService,
    PersistenceRequest,
    PersistenceResult,
    RejectedRecord,
    StudentAdapter,
    TeacherAdapter,
    RepresentativeAdapter,
    FinancialAdapter,
    simulated_db,
)


from apps.data_engine.events.base import BaseEventSubscriber


class MockEventSubscriber(BaseEventSubscriber):
    """Helper mock subscriber to capture events from EventBus."""

    def __init__(self) -> None:
        self.events: List[EventEnvelope] = []

    def on_event(self, envelope: EventEnvelope) -> None:
        self.events.append(envelope)



class TestTarea32IntegrationLayer(unittest.TestCase):
    """Test suite covering the TAREA 32 ERP Integration Layer."""

    def setUp(self) -> None:
        simulated_db.clear()
        IntegrationRegistry.global_registry().clear()
        # Re-register default adapters
        IntegrationRegistry.global_registry().register("student", StudentAdapter())
        IntegrationRegistry.global_registry().register("teacher", TeacherAdapter())
        IntegrationRegistry.global_registry().register("representative", RepresentativeAdapter())
        IntegrationRegistry.global_registry().register("financial", FinancialAdapter())
        EventBusRegistry.global_registry().reset()

    def tearDown(self) -> None:
        simulated_db.clear()
        IntegrationRegistry.global_registry().clear()
        EventBusRegistry.global_registry().reset()

    def test_dto_immutability(self) -> None:
        """Verify that integration DTOs are frozen/immutable."""
        mapping = EntityMapping(source_field="cedula", target_field="identification")
        with self.assertRaises(FrozenInstanceError):
            mapping.source_field = "new_field"  # type: ignore[misc]

        req = PersistenceRequest(entity_name="student", records=[])
        with self.assertRaises(FrozenInstanceError):
            req.entity_name = "teacher"  # type: ignore[misc]

        res = PersistenceResult(success=True)
        with self.assertRaises(FrozenInstanceError):
            res.success = False  # type: ignore[misc]

        rejected = RejectedRecord(record={}, reason="error")
        with self.assertRaises(FrozenInstanceError):
            rejected.reason = "another"  # type: ignore[misc]

        batch = BatchPersistenceResult(processed_count=0, success_count=0, failed_count=0)
        with self.assertRaises(FrozenInstanceError):
            batch.processed_count = 1  # type: ignore[misc]

    def test_registry_lifecycle_and_thread_safety(self) -> None:
        """Verify thread-safe singleton, register, unregister, exists, clear, and get."""
        registry = IntegrationRegistry.global_registry()
        self.assertTrue(registry.exists("student"))
        self.assertTrue(registry.exists("TEACHER"))  # Case insensitivity check

        # Unregister
        registry.unregister("student")
        self.assertFalse(registry.exists("student"))

        # Re-register
        adapter = StudentAdapter()
        registry.register("student", adapter)
        self.assertEqual(registry.get("Student"), adapter)

        # Clear
        registry.clear()
        self.assertFalse(registry.exists("teacher"))
        with self.assertRaises(AdapterNotFoundError):
            registry.get("student")

        # Thread safety verification
        registry.clear()
        results: List[Optional[Exception]] = []

        def worker(entity_name: str, a: Any) -> None:
            try:
                registry.register(entity_name, a)
            except Exception as e:
                results.append(e)

        threads = []
        for i in range(50):
            threads.append(threading.Thread(target=worker, args=(f"entity_{i}", StudentAdapter())))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 0)
        for i in range(50):
            self.assertTrue(registry.exists(f"entity_{i}"))

    def test_mappers_data_transformation(self) -> None:
        """Test mappers for conversion, defaults, upper/lower normalizations, etc."""
        # 1. Student Mapper
        reg_student = IntegrationRegistry.global_registry().get("student")
        student_mapper = reg_student.mapper
        res_student = student_mapper.map_record({
            "cedula": " 1723456789 ",
            "nombres": "john",
            "apellidos": "doe",
            "email": "JOHN.DOE@example.com",
            "telefono": "0999999999",
            "edad": "20",
        })
        self.assertEqual(res_student["identification"], "1723456789")
        self.assertEqual(res_student["first_name"], "JOHN")
        self.assertEqual(res_student["last_name"], "DOE")
        self.assertEqual(res_student["email"], "john.doe@example.com")
        self.assertEqual(res_student["phone"], "0999999999")
        self.assertEqual(res_student["age"], 20)

        # Student Mapper default value checks
        res_default_student = student_mapper.map_record({"cedula": "123"})
        self.assertEqual(res_default_student["phone"], "")
        self.assertEqual(res_default_student["age"], 0)

        # 2. Teacher Mapper
        reg_teacher = IntegrationRegistry.global_registry().get("teacher")
        teacher_mapper = reg_teacher.mapper
        res_teacher = teacher_mapper.map_record({
            "identificacion": "1723456781",
            "nombre_completo": "Jane Smith",
            "correo": "jane@smith.com",
            "especialidad": "Math",
        })
        self.assertEqual(res_teacher["identification"], "1723456781")
        self.assertEqual(res_teacher["full_name"], "JANE SMITH")
        self.assertEqual(res_teacher["email"], "jane@smith.com")
        self.assertEqual(res_teacher["specialty"], "Math")

        # 3. Representative Mapper
        reg_rep = IntegrationRegistry.global_registry().get("representative")
        rep_mapper = reg_rep.mapper
        res_rep = rep_mapper.map_record({
            "identificacion": "1723456782",
            "nombres": "robert",
            "apellidos": "doe",
        })
        self.assertEqual(res_rep["relationship"], "Padre")  # Default check

        # 4. Financial Mapper
        reg_fin = IntegrationRegistry.global_registry().get("financial")
        fin_mapper = reg_fin.mapper
        res_fin = fin_mapper.map_record({
            "codigo_rubro": "FEE001",
            "descripcion": "Enrollment fee",
            "valor": "150.75",
            "activo": "si",
        })
        self.assertEqual(res_fin["fee_code"], "FEE001")
        self.assertEqual(res_fin["amount"], 150.75)
        self.assertTrue(res_fin["is_active"])

    def test_persistence_adapter_operations(self) -> None:
        """Verify insertion, update, and rollback functionalities in the adapters."""
        adapter = IntegrationRegistry.global_registry().get("student")

        # Insert new record
        res1 = adapter.persist({"cedula": "1723456789", "nombres": "Alice", "apellidos": "Smith"})
        self.assertTrue(res1.success)
        self.assertEqual(res1.record_id, "1723456789")
        self.assertTrue(res1.created)

        # Retrieve database state
        table = simulated_db.tables["student"]
        self.assertEqual(len(table), 1)
        self.assertEqual(table[0]["first_name"], "ALICE")

        # Update existing record
        res2 = adapter.persist({"cedula": "1723456789", "nombres": "Alicia", "apellidos": "Smith"})
        self.assertTrue(res2.success)
        self.assertFalse(res2.created)
        self.assertEqual(table[0]["first_name"], "ALICIA")

        # Rollback check on batch failures
        batch_records = [
            {"cedula": "1111111111", "nombres": "Jack", "apellidos": "Doe"},
            {"cedula": "", "nombres": "Invalid", "apellidos": "Doe"},  # Missing cedula => error
        ]
        batch_res = adapter.persist_batch(batch_records)
        self.assertEqual(batch_res.failed_count, 2)
        # Verify transaction rolled back (no records added)
        self.assertEqual(len(simulated_db.tables.get("student", [])), 1)  # Only original Alice remains


    def test_transaction_manager(self) -> None:
        """Verify Transaction Manager commit, rollback, and context manager interface."""
        tx = InMemoryTransactionManager()
        self.assertFalse(tx.is_active)

        tx.begin()
        self.assertTrue(tx.is_active)
        tx.commit()
        self.assertTrue(tx.was_committed)
        self.assertFalse(tx.is_active)

        tx.begin()
        tx.rollback()
        self.assertTrue(tx.was_rolled_back)

        # Context manager check (Success => commit)
        with tx as t:
            self.assertTrue(t.is_active)
        self.assertTrue(tx.was_committed)

        # Context manager check (Exception => rollback)
        try:
            with tx as t:
                raise RuntimeError("Force Rollback")
        except RuntimeError:
            pass
        self.assertTrue(tx.was_rolled_back)

    def test_integration_service_success_flow(self) -> None:
        """Verify full success flow, progress updates, and EventBus publications."""
        sub = MockEventSubscriber()
        EventBusRegistry.global_registry().get_dispatcher().subscribe(sub)

        # Register session progress tracker
        tracker = ProgressTracker("session-123", run_id="run-123")
        ProgressRegistry.global_registry().register("run-123", tracker)

        records = [
            {"cedula": "1723456789", "nombres": "Alice", "apellidos": "Smith", "email": "alice@gmail.com"},
            {"cedula": "1723456788", "nombres": "Bob", "apellidos": "Jones", "email": "bob@gmail.com"},
        ]

        service = MacIntegrationService()
        result = service.integrate(
            entity_name="student",
            records=records,
            tenant_id="tenant-1",
            user_id="user-1",
            run_id="run-123",
        )

        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.failed_count, 0)

        # Verify database contents
        self.assertEqual(len(simulated_db.tables["student"]), 2)

        # Verify Progress Tracker updates
        snapshot = tracker.get_snapshot()
        self.assertEqual(snapshot.records_processed, 2)
        self.assertEqual(snapshot.records_accepted, 2)
        self.assertEqual(snapshot.records_rejected, 0)
        self.assertEqual(snapshot.current_phase, "Persistence Adapter")

        # Verify EventBus events published
        events = [e.event_type for e in sub.events]
        self.assertIn("PERSISTENCE_STARTED", events)
        self.assertIn("PERSISTENCE_COMPLETED", events)

    def test_integration_service_failure_flow(self) -> None:
        """Verify transaction rollback, progress recording, and event dispatch on failure."""
        sub = MockEventSubscriber()
        EventBusRegistry.global_registry().get_dispatcher().subscribe(sub)

        tracker = ProgressTracker("session-456", run_id="run-456")
        ProgressRegistry.global_registry().register("run-456", tracker)

        records = [
            {"cedula": "1723456789", "nombres": "Alice", "apellidos": "Smith"},
            {"cedula": "", "nombres": "Invalid", "apellidos": "Jones"},  # Fails mapping => rolls back both
        ]

        service = MacIntegrationService()
        result = service.integrate(
            entity_name="student",
            records=records,
            tenant_id="tenant-1",
            user_id="user-1",
            run_id="run-456",
        )

        self.assertEqual(result.failed_count, 2)
        # Database should be empty because of transaction rollback
        self.assertEqual(len(simulated_db.tables.get("student", [])), 0)

        # Progress tracker updates
        snapshot = tracker.get_snapshot()
        self.assertEqual(snapshot.records_processed, 2)
        self.assertEqual(snapshot.records_accepted, 0)
        self.assertEqual(snapshot.records_rejected, 2)

        # Events checking
        events = [e.event_type for e in sub.events]
        self.assertIn("PERSISTENCE_STARTED", events)
        self.assertIn("PERSISTENCE_FAILED", events)


class TestZeroOrmComplianceInIntegration(unittest.TestCase):
    """Verify Zero-ORM compliance in the integration package."""

    def test_integration_package_has_no_django_orm_dependencies(self) -> None:
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
