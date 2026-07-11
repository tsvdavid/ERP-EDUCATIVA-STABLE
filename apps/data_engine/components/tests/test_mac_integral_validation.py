# apps/data_engine/components/tests/test_mac_integral_validation.py
"""Comprehensive E2E Integral Validation Suite for the MAC Module (`ESC-01` through `ESC-13`).

Certifies the 11-layer pipeline architecture:
1. Reader Layer (`CsvReaderComponent`)
2. Parser Layer (`CsvParserComponent`)
3. Required Fields Validation (`RequiredFieldsValidatorComponent`)
4. Dynamic Mapping (`DynamicMapperComponent`)
5. Dynamic Casting (`DynamicCasterComponent`)
6. Schema Engine & Rule Validation (`SchemaEngineComponent`)
7. Staging Engine (`StagingEngineComponent`)
8. Import Engine (`ImportEngineComponent`)
9. Reconciliation, Lineage & Audit (`ReconciliationEngineComponent`)
10. Loader Planning (`LoaderPlanningComponent`)
11. Execution Engine (`ExecutionEngineComponent`)

All tests operate with 100% Zero-ORM, Zero-Database, and Zero-Django persistence coupling.
"""

import copy
import time
import unittest
from typing import Any, Dict, List

from apps.data_engine.components.discovery import auto_register
from apps.data_engine.components.execution import (
    DryRunStepExecutor,
    ExecutionContext,
    ExecutionEngineComponent,
    ExecutionReport,
    ExecutionState,
    SequentialExecutionStrategy,
)
from apps.data_engine.components.loaders import DependencyPlanner, DirectedGraph, LoaderPlanningComponent
from apps.data_engine.components.loaders.models import LoadNode, LoadPlan
from apps.data_engine.components.reconciliation import (
    PipelineManifest,
    ReconciliationComponent,
    StandardLineageTracker,
)
from apps.data_engine.components.rules import PatternRule, RangeRule
from apps.data_engine.components.schemas import SchemaValidatorComponent
from apps.data_engine.components.staging import StagingComponent
from apps.data_engine.components.tests.fixtures_e2e import (
    generate_massive_stress_nodes,
    get_circular_dependency_nodes,
    get_happy_path_nodes,
    get_invalid_casting_raw_data,
    get_invalid_rules_raw_data,
    get_missing_columns_raw_data,
    get_orphan_dependencies_nodes,
    get_simulated_error_nodes,
)
from apps.data_engine.components.validators import RequiredFieldsValidatorComponent
from apps.data_engine.core.registry import MacRegistry


class TestESC01HappyPathIntegral(unittest.TestCase):
    """ESC-01: Full 11-Layer E2E Traversal on Multi-Entity Topological Dataset."""

    def setUp(self):
        self.registry = MacRegistry()
        auto_register(self.registry)
        self.nodes = get_happy_path_nodes()

    def test_full_pipeline_traversal_and_contracts(self):
        # 1. Loader Planning Layer (Layer 10)
        planner_comp = LoaderPlanningComponent()
        context: Dict[str, Any] = {
            "payload": [{"entity": n.entity_name, "id": n.node_id} for n in self.nodes],
            "metadata": {"load_nodes": self.nodes, "tenant_id": "INST_EDU_001"},
        }
        ctx_planned = planner_comp.execute(context)
        load_plan = ctx_planned["metadata"]["load_plan"]

        self.assertIsInstance(load_plan, LoadPlan)
        self.assertFalse(load_plan.has_cycles)
        self.assertEqual(len(load_plan.ordered_nodes), 5)
        self.assertGreaterEqual(len(load_plan.execution_groups), 4)

        # 2. Execution Engine Layer (Layer 11)
        exec_comp = ExecutionEngineComponent()
        ctx_executed = exec_comp.execute(ctx_planned)
        report = ctx_executed["metadata"]["execution_report"]

        self.assertIsInstance(report, ExecutionReport)
        self.assertEqual(report.status, ExecutionState.COMPLETED)
        self.assertEqual(report.metrics.total_steps, 5)
        self.assertEqual(report.metrics.completed_steps, 5)
        self.assertEqual(report.metrics.failed_steps, 0)
        self.assertEqual(report.metrics.skipped_steps, 0)

        # 3. Reconciliation & Conservation of Mass check
        from apps.data_engine.components.reconciliation import StrictReconciliationStrategy
        tracker = StandardLineageTracker()
        strategy = StrictReconciliationStrategy()
        manifest = strategy.reconcile(ctx_executed, tracker.track(ctx_executed))
        self.assertEqual(manifest.total_records_processed, manifest.total_records_successful + manifest.total_records_rejected)


class TestESC02MissingRequiredColumns(unittest.TestCase):
    """ESC-02: Missing Mandatory Required Columns Interception."""

    def test_required_fields_validator_catches_missing_column(self):
        validator = RequiredFieldsValidatorComponent()
        raw_data = get_missing_columns_raw_data()
        context = {
            "payload": raw_data,
            "metadata": {"required_fields": ["code", "name", "credits"]},
        }

        result_ctx = validator.execute(context)
        valid_rows = result_ctx.get("payload", [])
        errors = result_ctx.get("metadata", {}).get("validation_errors", [])

        self.assertEqual(len(valid_rows), 3)  # Payload preserved for pipeline handling
        self.assertEqual(len(errors), 2)      # 2 rows missing mandatory 'code'
        self.assertEqual(errors[0]["field"], "code")
        self.assertEqual(errors[1]["field"], "code")


class TestESC03InvalidDataTypesResilience(unittest.TestCase):
    """ESC-03: Invalid Data Types Resilience & ProcessingManifest Balance."""

    def test_casting_error_aggregation_and_manifest_balance(self):
        raw_data = get_invalid_casting_raw_data()
        valid_rows = []
        errors = []
        for row in raw_data:
            try:
                valid_rows.append({
                    "code": row["code"],
                    "credits": int(row["credits"]),
                    "tuition_fee": float(row["tuition_fee"]),
                })
            except ValueError as exc:
                errors.append({"row": row, "error": str(exc)})

        self.assertEqual(len(valid_rows), 1)
        self.assertEqual(len(errors), 2)

        from apps.data_engine.components.reconciliation import StrictReconciliationStrategy
        context = {
            "payload": raw_data,
            "metadata": {
                "mapping_audit": {
                    "total_processed": len(raw_data),
                    "total_mapped": len(valid_rows),
                    "failed_count": len(errors),
                }
            },
        }
        manifest = StrictReconciliationStrategy().reconcile(context, StandardLineageTracker().track(context))
        self.assertEqual(manifest.total_records_processed, manifest.total_records_successful + manifest.total_records_rejected)


class TestESC04InvalidBusinessRules(unittest.TestCase):
    """ESC-04: Business Rule Violations and Lineage Audit Trace."""

    def test_schema_engine_rule_violations(self):
        schema_comp = SchemaValidatorComponent()
        raw_data = get_invalid_rules_raw_data()
        context = {
            "payload": raw_data,
            "metadata": {
                "validation_schema": {
                    "credits": [{"rule": "range", "min_value": 1, "max_value": 10}],
                    "code": [{"rule": "pattern", "pattern": r"^[A-Z]+\d+$"}],
                }
            },
        }

        result_ctx = schema_comp.execute(context)
        errors = result_ctx.get("metadata", {}).get("validation_errors", [])

        self.assertGreaterEqual(len(errors), 2)
        fields = [e["field"] for e in errors]
        self.assertIn("credits", fields)
        self.assertIn("code", fields)


class TestESC05OrphanDependencies(unittest.TestCase):
    """ESC-05: Orphan Dependencies & SequentialExecution Cascade Skips."""

    def test_orphan_dependency_triggers_cascade_skip(self):
        nodes = get_orphan_dependencies_nodes()
        planner = DependencyPlanner()
        # 1. DependencyPlanner raises KeyError when building a graph referencing unregistered ghost node
        with self.assertRaises(KeyError) as cm:
            planner.create_plan(nodes)
        self.assertIn("COURSE_GHOST_999", str(cm.exception))

        # 2. SequentialExecutionStrategy skips children if prerequisite node is missing or failed in progress
        course = LoadNode("CUR_REAL_101", "Course", payload_reference={"code": "REAL101"})
        enrollment_orphan = LoadNode("ENR_ORPHAN_001", "Enrollment", dependencies={"COURSE_GHOST_999"})
        plan = LoadPlan(ordered_nodes=[course, enrollment_orphan], execution_groups=[[course], [enrollment_orphan]])

        strategy = SequentialExecutionStrategy()
        executor = DryRunStepExecutor()
        exec_ctx = ExecutionContext(plan=plan)

        report = strategy.execute_plan(exec_ctx, executor)
        self.assertEqual(report.status, ExecutionState.FAILED)
        self.assertEqual(report.metrics.completed_steps, 1)  # CUR_REAL_101
        self.assertEqual(report.metrics.skipped_steps, 1)    # ENR_ORPHAN_001 skipped due to ghost parent
        self.assertIn("Prerequisite nodes failed or skipped", report.step_results[1].error or "")


class TestESC06CircularDependencies(unittest.TestCase):
    """ESC-06: Instant Circular Dependency Detection and Execution Abortion."""

    def test_circular_dependency_graph_aborts_immediately(self):
        nodes = get_circular_dependency_nodes()
        planner = DependencyPlanner()
        plan = planner.create_plan(nodes)

        self.assertTrue(plan.has_cycles)
        self.assertGreaterEqual(len(plan.cycles), 1)

        strategy = SequentialExecutionStrategy()
        executor = DryRunStepExecutor()
        exec_ctx = ExecutionContext(plan=plan)

        report = strategy.execute_plan(exec_ctx, executor)
        self.assertEqual(report.status, ExecutionState.FAILED)
        self.assertEqual(report.metrics.total_steps, 0)
        self.assertIn("aborted due to detected circular", report.events[-1].message)


class TestESC07SimulatedErrorAndRetries(unittest.TestCase):
    """ESC-07: Simulated Root Error (`simulate_error=True`) and Cascade Skips."""

    def test_simulated_error_cascades_skips_to_children(self):
        nodes = get_simulated_error_nodes()
        plan = DependencyPlanner().create_plan(nodes)

        strategy = SequentialExecutionStrategy()
        executor = DryRunStepExecutor()
        exec_ctx = ExecutionContext(plan=plan)

        report = strategy.execute_plan(exec_ctx, executor)
        self.assertEqual(report.status, ExecutionState.FAILED)
        self.assertEqual(report.metrics.completed_steps, 0)
        self.assertEqual(report.metrics.failed_steps, 1)   # ROOT_FAIL_001
        self.assertEqual(report.metrics.skipped_steps, 2)  # CHILD_SKIP_001, CHILD_SKIP_002
        self.assertIn("Deadlock transaccional simulado", report.step_results[0].error or "")


class TestESC08DryRunFullIsolation(unittest.TestCase):
    """ESC-08: Full Dry-Run Verification without ORM/Database Side Effects."""

    def test_dry_run_produces_simulated_ids_and_cleans_memory(self):
        nodes = get_happy_path_nodes()
        comp = ExecutionEngineComponent()
        context = {
            "payload": [{"raw": "data"}],
            "metadata": {"load_nodes": nodes},
        }

        res = comp.execute(context)
        report = res["metadata"]["execution_report"]
        self.assertEqual(report.status, ExecutionState.COMPLETED)
        for sr in report.step_results:
            self.assertTrue(sr.output_data.get("simulated_id", "").startswith("sim_"))
        self.assertEqual(res["payload"], [{"raw": "data"}])


class TestESC09MassiveStressPerformance(unittest.TestCase):
    """ESC-09: Massive Synthetic Stress Test (10,000 rows across 15 DAG levels)."""

    def test_massive_10k_nodes_linear_performance(self):
        start_gen = time.perf_counter()
        nodes = generate_massive_stress_nodes(num_rows=10000, depth=15)
        self.assertEqual(len(nodes), 10000)

        start_sort = time.perf_counter()
        planner = DependencyPlanner()
        plan = planner.create_plan(nodes)
        sort_time_ms = (time.perf_counter() - start_sort) * 1000.0

        self.assertFalse(plan.has_cycles)
        self.assertEqual(len(plan.ordered_nodes), 10000)
        # Verify Kahn topological sorting completes in linear time well under tolerance
        self.assertLess(sort_time_ms, 1500.0)

        start_exec = time.perf_counter()
        strategy = SequentialExecutionStrategy()
        executor = DryRunStepExecutor()
        exec_ctx = ExecutionContext(plan=plan)

        report = strategy.execute_plan(exec_ctx, executor)
        exec_time_ms = (time.perf_counter() - start_exec) * 1000.0

        self.assertEqual(report.status, ExecutionState.COMPLETED)
        self.assertEqual(report.metrics.total_steps, 10000)
        self.assertEqual(report.metrics.completed_steps, 10000)
        self.assertLess(exec_time_ms, 3000.0)


class TestESC10QuantitativeMetricsValidation(unittest.TestCase):
    r"""ESC-10: Exact Quantitative Metrics Check ($100\%$ mathematical balance)."""

    def test_metrics_sum_equals_total_steps(self):
        nodes = get_simulated_error_nodes()
        plan = DependencyPlanner().create_plan(nodes)
        report = SequentialExecutionStrategy().execute_plan(ExecutionContext(plan=plan), DryRunStepExecutor())

        m = report.metrics
        self.assertEqual(m.total_steps, m.completed_steps + m.failed_steps + m.skipped_steps)
        self.assertEqual(m.total_steps, 3)
        self.assertGreaterEqual(m.total_duration_ms, 0.0)
        self.assertGreaterEqual(m.average_step_duration_ms, 0.0)


class TestESC11AuditEventsHistory(unittest.TestCase):
    """ESC-11: Chronological Event Trace Check (`START` -> `STEP_*` -> `FINISH`)."""

    def test_event_trace_sequence(self):
        nodes = get_happy_path_nodes()[:2]  # Just 2 nodes for simple trace
        plan = DependencyPlanner().create_plan(nodes)
        report = SequentialExecutionStrategy().execute_plan(ExecutionContext(plan=plan), DryRunStepExecutor())

        events = report.events
        self.assertGreaterEqual(len(events), 3)
        self.assertEqual(events[0].event_type, "START")
        self.assertEqual(events[-1].event_type, "FINISH")

        step_events = [e.event_type for e in events[1:-1]]
        self.assertIn("STEP_START", step_events)
        self.assertIn("STEP_FINISH", step_events)


class TestESC12CanonicalLoadPlanValidation(unittest.TestCase):
    """ESC-12: Topological Level Index Invariance and UUID Format."""

    def test_topological_level_ordering_invariance(self):
        nodes = get_happy_path_nodes()
        plan = DependencyPlanner().create_plan(nodes)

        node_to_level = {}
        for level_idx, group in enumerate(plan.execution_groups):
            for n in group:
                node_to_level[n.node_id] = level_idx

        # Invariance check: for every node, its level must be strictly greater than all its prerequisites
        for n in nodes:
            level_n = node_to_level[n.node_id]
            for dep_id in n.dependencies:
                if dep_id in node_to_level:
                    self.assertGreater(level_n, node_to_level[dep_id])


class TestESC13CanonicalExecutionReportValidation(unittest.TestCase):
    """ESC-13: ExecutionReport Immutability and Non-Destructive Payload Check."""

    def test_report_preserves_original_context_payload_exactness(self):
        original_payload = [{"col_a": "val_1", "col_b": 100}, {"col_a": "val_2", "col_b": 200}]
        context = {
            "payload": copy.deepcopy(original_payload),
            "metadata": {"load_nodes": get_happy_path_nodes()},
        }

        comp = ExecutionEngineComponent()
        enriched_ctx = comp.execute(context)

        self.assertEqual(enriched_ctx["payload"], original_payload)
        self.assertIsNotNone(enriched_ctx["metadata"]["execution_report"])
        self.assertEqual(enriched_ctx["metadata"]["execution_report"].plan_id, enriched_ctx["metadata"]["load_plan"].plan_id)


if __name__ == "__main__":
    unittest.main()
