# apps/data_engine/components/tests/test_tarea16.py
"""Comprehensive Unit Test Suite for TAREA 16: Loader Engine & Dependency Resolution Framework.

Verifies:
1. Domain Models (`LoadNode`, `DependencyCycle`, `LoadPlan`) immutability and behavior.
2. Abstract Contracts (`BaseLoadPlanner`, `BaseDependencyResolver`, `BaseLoaderComponent`).
3. DirectedGraph DAG operations (`topological_sort` in O(V+E), `detect_cycles` via DFS).
4. DependencyPlanner (DAG resolution, execution level grouping, cycle handling).
5. LoaderPlanningComponent (Layer 10 pipeline execution, metadata attachment, non-destructive to payload).
6. Auto-Discovery (`discovery.py` registering `loader_planning_component`).
"""

import unittest
from typing import Any, Dict, List

from apps.data_engine.components.loaders import (
    BaseDependencyResolver,
    BaseLoaderComponent,
    BaseLoadPlanner,
    DependencyCycle,
    DependencyPlanner,
    DirectedGraph,
    LoaderPlanningComponent,
    LoadNode,
    LoadPlan,
)
from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.components.discovery import auto_register


class TestLoaderModelsContracts(unittest.TestCase):
    """Test domain dataclasses and abstract contract boundaries."""

    def test_load_node_creation_and_set_conversion(self):
        node = LoadNode(
            node_id="course_1",
            entity_name="Course",
            dependencies=["period_1", "inst_1"],  # Pass list to check __post_init__ set conversion
            payload_reference={"code": "MATH101"},
        )
        self.assertEqual(node.node_id, "course_1")
        self.assertEqual(node.entity_name, "Course")
        self.assertIsInstance(node.dependencies, set)
        self.assertEqual(node.dependencies, {"period_1", "inst_1"})
        self.assertEqual(node.payload_reference["code"], "MATH101")

    def test_dependency_cycle_creation(self):
        cycle = DependencyCycle(
            cycle_path=["A", "B", "C", "A"],
            message="Circular dependency detected",
        )
        self.assertEqual(cycle.cycle_path, ["A", "B", "C", "A"])
        self.assertIn("Circular", cycle.message)

    def test_load_plan_defaults_and_identifiers(self):
        plan = LoadPlan(ordered_nodes=[], execution_groups=[])
        self.assertFalse(plan.has_cycles)
        self.assertEqual(plan.total_nodes, 0)
        self.assertEqual(plan.cycles, [])
        self.assertIsNotNone(plan.plan_id)
        self.assertIsNotNone(plan.timestamp)

    def test_abstract_contracts_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            BaseLoadPlanner()
        with self.assertRaises(TypeError):
            BaseDependencyResolver()
        with self.assertRaises(TypeError):
            BaseLoaderComponent()


class TestDirectedGraph(unittest.TestCase):
    """Test DirectedGraph operations, Kahn's topological sort, and DFS cycle detection."""

    def setUp(self):
        self.graph = DirectedGraph()
        self.node_inst = LoadNode("inst_1", "Institution")
        self.node_period = LoadNode("period_1", "AcademicPeriod", {"inst_1"})
        self.node_course = LoadNode("course_1", "Course", {"period_1"})
        self.node_parallel = LoadNode("parallel_1", "Parallel", {"course_1"})
        self.node_student = LoadNode("student_1", "Student", {"parallel_1"})

    def test_add_node_and_edge_degrees(self):
        self.graph.add_node(self.node_inst)
        self.graph.add_node(self.node_period)
        self.graph.add_edge("inst_1", "period_1")

        self.assertEqual(self.graph.get_in_degree("inst_1"), 0)
        self.assertEqual(self.graph.get_out_degree("inst_1"), 1)
        self.assertEqual(self.graph.get_in_degree("period_1"), 1)
        self.assertEqual(self.graph.get_out_degree("period_1"), 0)
        self.assertEqual(self.graph.get_neighbors("inst_1"), {"period_1"})

    def test_missing_node_raises_key_error(self):
        self.graph.add_node(self.node_inst)
        with self.assertRaises(KeyError):
            self.graph.add_edge("inst_1", "non_existent")
        with self.assertRaises(KeyError):
            self.graph.get_neighbors("non_existent")
        with self.assertRaises(KeyError):
            self.graph.get_in_degree("non_existent")
        with self.assertRaises(KeyError):
            self.graph.get_out_degree("non_existent")
        with self.assertRaises(KeyError):
            self.graph.get_node("non_existent")

    def test_topological_sort_linear_chain(self):
        for n in [self.node_inst, self.node_period, self.node_course, self.node_parallel, self.node_student]:
            self.graph.add_node(n)
        
        self.graph.add_edge("inst_1", "period_1")
        self.graph.add_edge("period_1", "course_1")
        self.graph.add_edge("course_1", "parallel_1")
        self.graph.add_edge("parallel_1", "student_1")

        sorted_nodes = self.graph.topological_sort()
        ids = [n.node_id for n in sorted_nodes]
        self.assertEqual(ids, ["inst_1", "period_1", "course_1", "parallel_1", "student_1"])

    def test_topological_sort_multiple_roots_and_leaves(self):
        inst_a = LoadNode("inst_A", "Institution")
        inst_b = LoadNode("inst_B", "Institution")
        course_a = LoadNode("course_A", "Course")
        course_b = LoadNode("course_B", "Course")

        for n in [inst_a, inst_b, course_a, course_b]:
            self.graph.add_node(n)
        
        self.graph.add_edge("inst_A", "course_A")
        self.graph.add_edge("inst_B", "course_B")

        sorted_nodes = self.graph.topological_sort()
        ids = [n.node_id for n in sorted_nodes]
        self.assertEqual(len(ids), 4)
        # Verify both roots precede their respective leaves
        self.assertLess(ids.index("inst_A"), ids.index("course_A"))
        self.assertLess(ids.index("inst_B"), ids.index("course_B"))

    def test_detect_cycles_direct(self):
        node_a = LoadNode("A", "EntityA")
        node_b = LoadNode("B", "EntityB")
        self.graph.add_node(node_a)
        self.graph.add_node(node_b)
        self.graph.add_edge("A", "B")
        self.graph.add_edge("B", "A")

        cycles = self.graph.detect_cycles()
        self.assertEqual(len(cycles), 1)
        self.assertIn("A -> B -> A", cycles[0].message)

        # Topological sort should raise ValueError when cycles exist
        with self.assertRaises(ValueError):
            self.graph.topological_sort()

    def test_detect_cycles_indirect_chain(self):
        node_x = LoadNode("X", "EntityX")
        node_y = LoadNode("Y", "EntityY")
        node_z = LoadNode("Z", "EntityZ")
        for n in [node_x, node_y, node_z]:
            self.graph.add_node(n)
        self.graph.add_edge("X", "Y")
        self.graph.add_edge("Y", "Z")
        self.graph.add_edge("Z", "X")

        cycles = self.graph.detect_cycles()
        self.assertGreaterEqual(len(cycles), 1)
        self.assertIn("X -> Y -> Z -> X", cycles[0].message)


class TestDependencyPlanner(unittest.TestCase):
    """Test DependencyPlanner orchestration, execution grouping, and LoadPlan generation."""

    def setUp(self):
        self.planner = DependencyPlanner()

    def test_create_plan_valid_dag_with_execution_groups(self):
        # Level 0
        inst = LoadNode("inst_1", "Institution", set())
        # Level 1
        period_a = LoadNode("period_A", "AcademicPeriod", {"inst_1"})
        period_b = LoadNode("period_B", "AcademicPeriod", {"inst_1"})
        # Level 2
        course = LoadNode("course_1", "Course", {"period_A", "period_B"})

        nodes = [course, period_b, inst, period_a]  # Shuffled input order
        plan = self.planner.create_plan(nodes)

        self.assertFalse(plan.has_cycles)
        self.assertEqual(plan.total_nodes, 4)
        self.assertEqual(len(plan.cycles), 0)

        # Verify execution groups by level
        self.assertEqual(len(plan.execution_groups), 3)
        group_0_ids = {n.node_id for n in plan.execution_groups[0]}
        group_1_ids = {n.node_id for n in plan.execution_groups[1]}
        group_2_ids = {n.node_id for n in plan.execution_groups[2]}

        self.assertEqual(group_0_ids, {"inst_1"})
        self.assertEqual(group_1_ids, {"period_A", "period_B"})
        self.assertEqual(group_2_ids, {"course_1"})

    def test_create_plan_with_cycles_returns_has_cycles_true(self):
        node_1 = LoadNode("node_1", "Entity1", {"node_2"})
        node_2 = LoadNode("node_2", "Entity2", {"node_1"})

        plan = self.planner.create_plan([node_1, node_2])
        self.assertTrue(plan.has_cycles)
        self.assertEqual(plan.total_nodes, 2)
        self.assertEqual(len(plan.ordered_nodes), 0)
        self.assertEqual(len(plan.execution_groups), 0)
        self.assertGreaterEqual(len(plan.cycles), 1)


class TestLoaderComponentIntegration(unittest.TestCase):
    """Test LoaderPlanningComponent execution and pipeline behavior."""

    def setUp(self):
        self.component = LoaderPlanningComponent()

    def test_execute_with_explicit_load_nodes_in_metadata(self):
        nodes = [
            LoadNode("inst_1", "Institution"),
            LoadNode("period_1", "AcademicPeriod", {"inst_1"}),
        ]
        context = {
            "payload": {"rawData": "abc"},
            "metadata": {"load_nodes": nodes, "tenant_id": "tenant_xyz"},
        }

        result = self.component.execute(context)
        self.assertIn("load_plan", result["metadata"])
        plan = result["metadata"]["load_plan"]
        self.assertIsInstance(plan, LoadPlan)
        self.assertFalse(plan.has_cycles)
        self.assertEqual(plan.total_nodes, 2)
        self.assertEqual(result["payload"], {"rawData": "abc"})  # Payload untouched

    def test_execute_insects_default_node_when_metadata_missing_nodes(self):
        context = {
            "payload": {"name": "Test Course"},
            "metadata": {"target_entity": "Course"},
        }

        result = self.component.execute(context)
        plan = result["metadata"]["load_plan"]
        self.assertEqual(plan.total_nodes, 1)
        self.assertEqual(plan.ordered_nodes[0].entity_name, "Course")
        self.assertEqual(plan.ordered_nodes[0].payload_reference, {"name": "Test Course"})

    def test_execute_invalid_context_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.component.execute("not_a_dict")  # type: ignore

    def test_invalid_planner_injection_raises_type_error(self):
        with self.assertRaises(TypeError):
            LoaderPlanningComponent(planner="invalid_object")  # type: ignore

    def test_auto_discovery_registers_loader_component(self):
        registry = MacRegistry()
        auto_register(registry)
        component = registry.get("loader_planning_component")
        self.assertIsNotNone(component)
        self.assertIsInstance(component, LoaderPlanningComponent)


if __name__ == "__main__":
    unittest.main()
