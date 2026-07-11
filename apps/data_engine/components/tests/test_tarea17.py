# apps/data_engine/components/tests/test_tarea17.py
"""Comprehensive Unit Test Suite for TAREA 17: Execution Engine & Load Execution Framework.

Verifies:
1. Domain Models (`ExecutionState`, `ExecutionEvent`, `ExecutionStep`, `ExecutionResult`, `ExecutionMetrics`, `ExecutionReport`, `ExecutionContext`).
2. Abstract Contracts (`BaseStepExecutor`, `BaseExecutionStrategy`, `BaseExecutionEventListener`, `BaseExecutionEngine`).
3. DryRunStepExecutor (simulated memory execution without database coupling, simulated failures via payload flags).
4. SequentialExecutionStrategy (topological level traversal, prerequisite checking and cascade skips, abort handling, cyclic plans).
5. ExecutionEngineComponent (Layer 11 pipeline adapter, metadata attachment, non-destructive to payload).
6. Auto-Discovery (`discovery.py` registering `execution_engine_component`).
"""

import unittest
from typing import Any, Dict

from apps.data_engine.components.execution import (
    BaseExecutionEngine,
    BaseExecutionEventListener,
    BaseExecutionStrategy,
    BaseStepExecutor,
    DryRunStepExecutor,
    ExecutionContext,
    ExecutionEngineComponent,
    ExecutionEvent,
    ExecutionMetrics,
    ExecutionReport,
    ExecutionResult,
    ExecutionState,
    ExecutionStep,
    SequentialExecutionStrategy,
)
from apps.data_engine.components.loaders.models import DependencyCycle, LoadNode, LoadPlan
from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.components.discovery import auto_register


class TestExecutionModelsContracts(unittest.TestCase):
    """Test domain models, enums, memory container, and abstract boundaries."""

    def test_execution_state_enum_values(self):
        self.assertEqual(ExecutionState.PENDING.value, "PENDING")
        self.assertEqual(ExecutionState.RUNNING.value, "RUNNING")
        self.assertEqual(ExecutionState.COMPLETED.value, "COMPLETED")
        self.assertEqual(ExecutionState.FAILED.value, "FAILED")
        self.assertEqual(ExecutionState.SKIPPED.value, "SKIPPED")
        self.assertEqual(ExecutionState.ABORTED.value, "ABORTED")

    def test_execution_event_and_context_record_event(self):
        plan = LoadPlan()
        ctx = ExecutionContext(plan=plan)
        ctx.record_event("STEP_START", "Starting node_a", node_id="node_a", metadata={"key": "val"})

        self.assertEqual(len(ctx.events), 1)
        ev = ctx.events[0]
        self.assertEqual(ev.event_type, "STEP_START")
        self.assertEqual(ev.node_id, "node_a")
        self.assertEqual(ev.message, "Starting node_a")
        self.assertEqual(ev.metadata, {"key": "val"})
        self.assertIsNotNone(ev.timestamp)

    def test_execution_step_and_result_defaults(self):
        node = LoadNode("node_1", "Entity1")
        step = ExecutionStep("step_xyz", node)
        self.assertEqual(step.state, ExecutionState.PENDING)
        self.assertEqual(step.attempts, 0)

        res = ExecutionResult(
            success=True,
            step_id="step_xyz",
            node_id="node_1",
            state=ExecutionState.COMPLETED,
        )
        self.assertTrue(res.success)
        self.assertEqual(res.output_data, {})
        self.assertIsNone(res.error)

    def test_abstract_contracts_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            BaseStepExecutor()
        with self.assertRaises(TypeError):
            BaseExecutionStrategy()
        with self.assertRaises(TypeError):
            BaseExecutionEventListener()
        with self.assertRaises(TypeError):
            BaseExecutionEngine()


class TestDryRunStepExecutor(unittest.TestCase):
    """Test DryRunStepExecutor simulated processing and error handling."""

    def setUp(self):
        self.executor = DryRunStepExecutor()
        self.plan = LoadPlan()
        self.ctx = ExecutionContext(plan=self.plan)

    def test_execute_step_success_preserves_dict_payload(self):
        node = LoadNode(
            node_id="course_1",
            entity_name="Course",
            payload_reference={"code": "MATH101", "credits": 4},
        )
        step = ExecutionStep("step_1", node)
        result = self.executor.execute_step(step, self.ctx)

        self.assertTrue(result.success)
        self.assertEqual(result.state, ExecutionState.COMPLETED)
        self.assertEqual(result.output_data["code"], "MATH101")
        self.assertEqual(result.output_data["credits"], 4)
        self.assertEqual(result.output_data["simulated_id"], "sim_course_1")
        self.assertGreaterEqual(result.execution_time_ms, 0.0)

    def test_execute_step_simulated_error_flag(self):
        node = LoadNode(
            node_id="course_fail",
            entity_name="Course",
            payload_reference={"simulate_error": True, "error_message": "Invalid credits validation"},
        )
        step = ExecutionStep("step_fail", node)
        result = self.executor.execute_step(step, self.ctx)

        self.assertFalse(result.success)
        self.assertEqual(result.state, ExecutionState.FAILED)
        self.assertIn("Invalid credits validation", result.error or "")


class TestSequentialExecutionStrategy(unittest.TestCase):
    """Test SequentialExecutionStrategy topological traversal and cascade skips."""

    def setUp(self):
        self.strategy = SequentialExecutionStrategy()
        self.executor = DryRunStepExecutor()

    def test_execute_plan_happy_path(self):
        inst = LoadNode("inst_1", "Institution")
        period = LoadNode("period_1", "AcademicPeriod", {"inst_1"})
        course = LoadNode("course_1", "Course", {"period_1"})

        plan = LoadPlan(
            ordered_nodes=[inst, period, course],
            execution_groups=[[inst], [period], [course]],
        )
        ctx = ExecutionContext(plan=plan)

        report = self.strategy.execute_plan(ctx, self.executor)
        self.assertEqual(report.status, ExecutionState.COMPLETED)
        self.assertEqual(report.metrics.total_steps, 3)
        self.assertEqual(report.metrics.completed_steps, 3)
        self.assertEqual(report.metrics.failed_steps, 0)
        self.assertEqual(report.metrics.skipped_steps, 0)
        self.assertEqual(ctx.step_progress["course_1"], ExecutionState.COMPLETED)

    def test_execute_plan_prerequisite_failure_cascades_to_skips(self):
        inst = LoadNode("inst_1", "Institution", payload_reference={"simulate_error": True, "error_message": "DB Down"})
        period = LoadNode("period_1", "AcademicPeriod", {"inst_1"})
        course = LoadNode("course_1", "Course", {"period_1"})

        plan = LoadPlan(
            ordered_nodes=[inst, period, course],
            execution_groups=[[inst], [period], [course]],
        )
        ctx = ExecutionContext(plan=plan)

        report = self.strategy.execute_plan(ctx, self.executor)
        self.assertEqual(report.status, ExecutionState.FAILED)
        self.assertEqual(report.metrics.total_steps, 3)
        self.assertEqual(report.metrics.completed_steps, 0)
        self.assertEqual(report.metrics.failed_steps, 1)    # inst_1
        self.assertEqual(report.metrics.skipped_steps, 2)   # period_1, course_1

        self.assertEqual(ctx.step_progress["inst_1"], ExecutionState.FAILED)
        self.assertEqual(ctx.step_progress["period_1"], ExecutionState.SKIPPED)
        self.assertEqual(ctx.step_progress["course_1"], ExecutionState.SKIPPED)

    def test_execute_plan_aborted_by_cycles(self):
        plan = LoadPlan(has_cycles=True, cycles=[DependencyCycle(["A", "A"], "Cycle")])
        ctx = ExecutionContext(plan=plan)

        report = self.strategy.execute_plan(ctx, self.executor)
        self.assertEqual(report.status, ExecutionState.FAILED)
        self.assertEqual(report.metrics.total_steps, 0)
        self.assertIn("aborted due to detected circular", report.events[-1].message)

    def test_execute_plan_abort_flag_set(self):
        inst_a = LoadNode("inst_a", "Institution")
        inst_b = LoadNode("inst_b", "Institution")
        plan = LoadPlan(execution_groups=[[inst_a], [inst_b]])
        ctx = ExecutionContext(plan=plan, is_aborted=True)

        report = self.strategy.execute_plan(ctx, self.executor)
        self.assertEqual(report.status, ExecutionState.ABORTED)


class TestExecutionEngineComponent(unittest.TestCase):
    """Test Layer 11 pipeline adapter behavior."""

    def setUp(self):
        self.component = ExecutionEngineComponent()

    def test_execute_with_existing_load_plan(self):
        inst = LoadNode("inst_1", "Institution")
        plan = LoadPlan(execution_groups=[[inst]])
        context = {
            "payload": {"data": "test"},
            "metadata": {"load_plan": plan},
        }

        result = self.component.execute(context)
        self.assertIn("execution_report", result["metadata"])
        report = result["metadata"]["execution_report"]
        self.assertIsInstance(report, ExecutionReport)
        self.assertEqual(report.status, ExecutionState.COMPLETED)
        self.assertEqual(result["payload"], {"data": "test"})  # Unaltered

    def test_execute_infers_plan_when_missing(self):
        context = {
            "payload": {"code": "ENG101"},
            "metadata": {"target_entity": "Course"},
        }

        result = self.component.execute(context)
        report = result["metadata"]["execution_report"]
        self.assertEqual(report.metrics.total_steps, 1)
        self.assertEqual(report.step_results[0].output_data["code"], "ENG101")

    def test_execute_invalid_context_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.component.execute("not_a_dict")  # type: ignore

    def test_invalid_constructor_args_raise_type_error(self):
        with self.assertRaises(TypeError):
            ExecutionEngineComponent(strategy="invalid")  # type: ignore
        with self.assertRaises(TypeError):
            ExecutionEngineComponent(executor="invalid")  # type: ignore

    def test_auto_discovery_registers_execution_engine(self):
        registry = MacRegistry()
        auto_register(registry)
        comp = registry.get("execution_engine_component")
        self.assertIsNotNone(comp)
        self.assertIsInstance(comp, ExecutionEngineComponent)


if __name__ == "__main__":
    unittest.main()
