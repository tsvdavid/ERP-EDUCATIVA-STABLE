# apps/data_engine/jobs/tests/test_tarea24.py
"""Comprehensive Test Suite for Background Processing & Distributed Job Framework (TAREA 24).

Verifies:
1. Domain contracts and model immutability (`JobStatus`, `JobConfig`, `JobRecord`).
2. In-Memory adapters (`InMemoryJobStore`, `InMemoryJobQueue`) and `CeleryJobAdapter` contracts.
3. `JobManager` lifecycle transitions (`QUEUED` -> `RUNNING` -> `COMPLETED`/`FAILED`/`RETRYING`).
4. Automatic retry policies and exponential/configurable backoff logic.
5. Job cancellation (`CANCELLED`) and manual retry capabilities.
6. Real-time Event Bus notifications (`JOB_QUEUED`, `JOB_STARTED`, `JOB_COMPLETED`, etc.).
7. Zero-ORM enforcement across the entire `jobs/` package via static AST inspection.
"""

import ast
import os
import time
from unittest.mock import MagicMock, patch
import pytest

from apps.data_engine.application.exceptions import ImportException, ValidationException
from apps.data_engine.components.base import BaseComponent
from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.events.models import EventCategory
from apps.data_engine.events.registry import EventBusRegistry
from apps.data_engine.events.subscribers import InMemoryEventSubscriber
from apps.data_engine.jobs.adapters import CeleryJobAdapter, InMemoryJobQueue, InMemoryJobStore
from apps.data_engine.jobs.contracts import JobConfig, JobRecord, JobStatus
from apps.data_engine.jobs.exceptions import (
    JobCancelledException,
    JobException,
    JobNotFoundException,
)
from apps.data_engine.jobs.manager import JobManager
from apps.data_engine.jobs.registry import JobRegistry
from apps.data_engine.jobs.tasks import run_mac_job


# ==============================================================================
# Mocks & Helper Fixtures
# ==============================================================================

class MockReader(BaseComponent):
    def get_name(self) -> str:
        return "mock_reader"

    def execute(self, context: dict) -> dict:
        records = [{"id": 1, "val": 10}, {"id": 2, "val": 20}]
        return {"payload": {"raw_data": records}}


class MockParser(BaseComponent):
    def get_name(self) -> str:
        return "mock_parser"

    def execute(self, context: dict) -> dict:
        records = [{"id": 1, "val": 10}, {"id": 2, "val": 20}]
        return {"payload": {"parsed_records": records, "raw_data": records}}


class FlakyReader(BaseComponent):
    """Component that fails once with ImportException, then succeeds on retry."""
    attempt_counter = 0

    def get_name(self) -> str:
        return "flaky_reader"

    def execute(self, context: dict) -> dict:
        FlakyReader.attempt_counter += 1
        if FlakyReader.attempt_counter == 1:
            raise ImportException("Simulated temporary connection timeout reading CSV.")
        records = [{"id": 1, "val": 10}]
        return {"payload": {"raw_data": records}}


@pytest.fixture(autouse=True)
def setup_job_test_environment():
    """Reset registries and attach EventBus subscriber before each test."""
    JobRegistry.reset_global_registry()
    JobManager.reset_global_instance()
    EventBusRegistry.global_registry().reset()

    MacRegistry.global_registry().register("mock_reader", MockReader())
    MacRegistry.global_registry().register("mock_parser", MockParser())
    FlakyReader.attempt_counter = 0
    MacRegistry.global_registry().register("flaky_reader", FlakyReader())

    subscriber = InMemoryEventSubscriber()
    EventBusRegistry.global_registry().get_dispatcher().subscribe(subscriber)
    yield
    JobRegistry.reset_global_registry()
    JobManager.reset_global_instance()
    EventBusRegistry.global_registry().reset()


# ==============================================================================
# 1. Domain Contracts & Models
# ==============================================================================

class TestJobModelsAndContracts:
    def test_job_status_enum_values(self):
        assert JobStatus.QUEUED.value == "QUEUED"
        assert JobStatus.RUNNING.value == "RUNNING"
        assert JobStatus.RETRYING.value == "RETRYING"
        assert JobStatus.COMPLETED.value == "COMPLETED"
        assert JobStatus.FAILED.value == "FAILED"
        assert JobStatus.CANCELLED.value == "CANCELLED"

    def test_job_config_defaults_and_immutability(self):
        cfg = JobConfig()
        assert cfg.queue_name == "mac_jobs"
        assert cfg.max_retries == 3
        assert cfg.retry_delay_seconds == 60
        assert cfg.timeout_seconds == 3600
        assert cfg.priority == 0

        with pytest.raises(AttributeError):
            cfg.max_retries = 10

    def test_job_record_with_status_immutability(self):
        rec = JobRecord(
            job_id="job-100",
            session_id="sess-100",
            tenant_id="tenant_x",
            user_id="user_x",
            status=JobStatus.QUEUED,
        )
        assert rec.status == JobStatus.QUEUED
        assert rec.retry_count == 0

        updated = rec.with_status(status=JobStatus.RUNNING, started_at=1000.0)
        assert updated.status == JobStatus.RUNNING
        assert updated.started_at == 1000.0
        assert rec.status == JobStatus.QUEUED  # Original remains intact


# ==============================================================================
# 2. In-Memory & Celery Adapters
# ==============================================================================

class TestInMemoryAdapters:
    def test_in_memory_store_operations(self):
        store = InMemoryJobStore()
        rec = JobRecord(job_id="j-1", session_id="s-1", tenant_id="t-1", user_id="u-1")
        store.save(rec)

        loaded = store.get("j-1")
        assert loaded is not None
        assert loaded.job_id == "j-1"

        tenant_jobs = store.list_by_tenant("t-1")
        assert len(tenant_jobs) == 1
        assert store.list_by_tenant("t-2") == []

        assert store.delete("j-1") is True
        assert store.get("j-1") is None
        assert store.delete("j-1") is False

    def test_in_memory_queue_operations(self):
        queue = InMemoryJobQueue()
        cfg = JobConfig()
        qid = queue.enqueue("j-1", cfg, delay_seconds=0, source="test.csv")
        assert qid == "j-1"
        assert "j-1" in queue.queued_tasks

        assert queue.cancel("j-1") is True
        assert "j-1" not in queue.queued_tasks
        assert "j-1" in queue.cancelled_job_ids


class TestCeleryJobAdapter:
    def test_celery_adapter_enqueue_and_cancel_with_mock_app(self):
        mock_celery = MagicMock()
        mock_async_res = MagicMock()
        mock_async_res.id = "celery-task-999"
        mock_celery.send_task.return_value = mock_async_res

        adapter = CeleryJobAdapter(celery_app=mock_celery)
        cfg = JobConfig(queue_name="priority_q", priority=5)

        task_id = adapter.enqueue("j-123", cfg, delay_seconds=30, source="big.csv")
        assert task_id == "celery-task-999"

        mock_celery.send_task.assert_called_once_with(
            "apps.data_engine.jobs.tasks.run_mac_job",
            args=["j-123"],
            kwargs={"source": "big.csv"},
            queue="priority_q",
            countdown=30,
            priority=5,
        )

        assert adapter.cancel("j-123", task_id="celery-task-999") is True
        mock_celery.control.revoke.assert_called_once_with("celery-task-999", terminate=True)


# ==============================================================================
# 3. JobManager Lifecycle & Automatic Retries
# ==============================================================================

class TestJobManagerLifecycleAndRetries:
    def test_create_and_run_happy_path(self):
        manager = JobManager.global_instance()
        record = manager.create_and_enqueue(
            tenant_id="tenant_happy",
            user_id="user_1",
            source="stream.csv",
            pipeline_config={"reader": ["mock_reader"], "parser": ["mock_parser"]},
        )
        assert record.status == JobStatus.QUEUED

        # Run via runner / worker task wrapper
        result = run_mac_job(record.job_id, source="stream.csv", pipeline_config={"reader": ["mock_reader"], "parser": ["mock_parser"]})
        assert result["is_success"] is True

        updated = manager.get_job(record.job_id)
        assert updated.status == JobStatus.COMPLETED
        assert updated.finished_at is not None

        # Verify EventBus events emitted
        dispatcher = EventBusRegistry.global_registry().get_dispatcher()
        subscribers = dispatcher._subscribers
        in_mem_sub = next(s for s in subscribers if isinstance(s, InMemoryEventSubscriber))
        events = in_mem_sub.get_events_by_session(record.session_id)
        event_types = [ev.event_type for ev in events]

        assert "JOB_QUEUED" in event_types
        assert "JOB_STARTED" in event_types
        assert "JOB_COMPLETED" in event_types

    def test_automatic_retry_on_recoverable_failure(self):
        manager = JobManager.global_instance()
        cfg = JobConfig(max_retries=2, retry_delay_seconds=10)
        record = manager.create_and_enqueue(
            tenant_id="tenant_retry",
            user_id="user_2",
            source="stream.csv",
            pipeline_config={"reader": ["flaky_reader"], "parser": ["mock_parser"]},
            config=cfg,
        )

        # 1st Attempt -> FlakyReader raises ImportException -> manager catches and transitions to RETRYING
        res1 = manager.run_job(
            record.job_id,
            source="stream.csv",
            pipeline_config={"reader": ["flaky_reader"], "parser": ["mock_parser"]},
        )
        assert res1["status"] == "RETRYING"
        assert res1["retry_count"] == 1

        rec_after_1 = manager.get_job(record.job_id)
        assert rec_after_1.status == JobStatus.RETRYING
        assert rec_after_1.retry_count == 1
        assert "timeout" in rec_after_1.error_message.lower()

        # 2nd Attempt (Retry run) -> FlakyReader succeeds -> manager transitions to COMPLETED
        res2 = manager.run_job(
            record.job_id,
            source="stream.csv",
            pipeline_config={"reader": ["flaky_reader"], "parser": ["mock_parser"]},
            is_resume=True,
        )
        assert res2["is_success"] is True

        rec_final = manager.get_job(record.job_id)
        assert rec_final.status == JobStatus.COMPLETED
        assert rec_final.retry_count == 1

        # Verify EventBus notifications included RETRYING
        dispatcher = EventBusRegistry.global_registry().get_dispatcher()
        subscribers = dispatcher._subscribers
        in_mem_sub = next(s for s in subscribers if isinstance(s, InMemoryEventSubscriber))
        events = in_mem_sub.get_events_by_session(record.session_id)
        event_types = [ev.event_type for ev in events]

        assert "JOB_RETRYING" in event_types
        assert "JOB_COMPLETED" in event_types

    def test_max_retries_exceeded_transitions_to_failed(self):
        manager = JobManager.global_instance()
        cfg = JobConfig(max_retries=1)
        record = manager.create_and_enqueue(
            tenant_id="tenant_fail",
            user_id="user_3",
            source="stream.csv",
            pipeline_config={"reader": ["flaky_reader"], "parser": ["mock_parser"]},
            config=cfg,
        )

        # 1st Attempt -> fails -> RETRYING (retry_count = 1)
        manager.run_job(
            record.job_id,
            source="stream.csv",
            pipeline_config={"reader": ["flaky_reader"], "parser": ["mock_parser"]},
        )
        # Reset counter to simulate persistent failure
        FlakyReader.attempt_counter = 0

        # 2nd Attempt -> fails -> retry_count (1) >= max_retries (1) -> FAILED
        res_fail = manager.run_job(
            record.job_id,
            source="stream.csv",
            pipeline_config={"reader": ["flaky_reader"], "parser": ["mock_parser"]},
        )
        assert res_fail["status"] == "FAILED"

        rec_final = manager.get_job(record.job_id)
        assert rec_final.status == JobStatus.FAILED
        assert rec_final.finished_at is not None

    def test_cancel_job_prevents_execution(self):
        manager = JobManager.global_instance()
        record = manager.create_and_enqueue(
            tenant_id="tenant_cancel",
            user_id="user_4",
            source="stream.csv",
        )
        cancelled = manager.cancel_job(record.job_id)
        assert cancelled.status == JobStatus.CANCELLED

        with pytest.raises(JobCancelledException):
            manager.run_job(record.job_id)

    def test_manual_retry_job(self):
        manager = JobManager.global_instance()
        record = manager.create_and_enqueue(tenant_id="tenant_manual", user_id="user_5", source="stream.csv")
        store = JobRegistry.global_registry().get_store()
        store.save(record.with_status(JobStatus.FAILED, error_message="Fatal crash"))

        retried = manager.retry_job(record.job_id)
        assert retried.status == JobStatus.QUEUED
        assert retried.retry_count == 1
        assert retried.error_message is None


# ==============================================================================
# 4. Zero-ORM Enforcement in `jobs/` Package
# ==============================================================================

class TestZeroOrmComplianceInJobs:
    """Verify via static AST inspection that `jobs/` has no Django ORM dependencies."""

    def test_jobs_package_has_no_django_orm_dependencies(self):
        jobs_dir = os.path.join(os.path.dirname(__file__), "..")
        jobs_dir = os.path.abspath(jobs_dir)

        forbidden_modules = ("django.db", "django.contrib", "django.core")

        for root, _, files in os.walk(jobs_dir):
            if "tests" in root.split(os.sep):
                continue
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=filepath)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                for forbidden in forbidden_modules:
                                    if alias.name.startswith(forbidden):
                                        pytest.fail(f"Zero-ORM violation: {filepath} imports {alias.name}")
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                for forbidden in forbidden_modules:
                                    if node.module.startswith(forbidden):
                                        pytest.fail(f"Zero-ORM violation: {filepath} imports from {node.module}")
