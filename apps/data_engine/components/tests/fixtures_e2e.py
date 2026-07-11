# apps/data_engine/components/tests/fixtures_e2e.py
"""Canonical E2E Fixtures and Synthetic Dataset Generators for MAC Integral Validation.

Provides pure-python fixtures (raw dictionaries, CSV strings, and `LoadNode` instances)
to evaluate the 11 layers of the MAC pipeline across normal, error-handling, resilience,
circular dependency, and stress-testing scenarios (`ESC-01` through `ESC-09`) without ORM coupling.
"""

from typing import Any, Dict, List
from apps.data_engine.components.loaders.models import LoadNode


def get_happy_path_nodes() -> List[LoadNode]:
    """ESC-01: Multi-entity topological happy-path dataset.

    Hierarchy: Institution -> AcademicPeriod -> Course -> Student -> Enrollment.
    Returns:
        List of 5 ordered `LoadNode` objects with consistent prerequisite dependencies.
    """
    inst = LoadNode(
        node_id="INST_EDU_001",
        entity_name="Institution",
        payload_reference={"name": "Colegio Prisca Eduka360", "tax_id": "800999111-2", "status": "ACTIVE"},
    )
    period = LoadNode(
        node_id="PER_2026_S1",
        entity_name="AcademicPeriod",
        dependencies={"INST_EDU_001"},
        payload_reference={"period_code": "2026-S1", "start_date": "2026-01-15", "end_date": "2026-06-30"},
    )
    course = LoadNode(
        node_id="CUR_MATH_101",
        entity_name="Course",
        dependencies={"PER_2026_S1"},
        payload_reference={"code": "MATH101", "name": "Álgebra Lineal Avanzada", "credits": 4, "quota": 30},
    )
    student = LoadNode(
        node_id="STU_ALEX_889",
        entity_name="Student",
        dependencies={"INST_EDU_001"},
        payload_reference={"document_id": "DOC_88921", "full_name": "Alexander Hamilton", "email": "alex@eduka360.org"},
    )
    enrollment = LoadNode(
        node_id="ENR_MATH_ALEX",
        entity_name="Enrollment",
        dependencies={"CUR_MATH_101", "STU_ALEX_889"},
        payload_reference={"enrollment_date": "2026-01-20", "status": "CONFIRMED"},
    )
    return [inst, period, course, student, enrollment]


def get_missing_columns_raw_data() -> List[Dict[str, Any]]:
    """ESC-02: Missing mandatory required columns in raw dataset.

    Intentionally omits the mandatory `code` field to test `RequiredFieldsValidatorComponent`.
    Returns:
        List of raw dictionaries with missing required keys.
    """
    return [
        {"name": "Física Mecánica", "credits": "4", "quota": "25"},
        {"code": "CHEM101", "name": "Química General", "credits": "3", "quota": "20"},
        {"name": "Biología Celular", "credits": "3", "quota": "15"},  # Missing code
    ]


def get_invalid_casting_raw_data() -> List[Dict[str, Any]]:
    """ESC-03: Invalid data types for casting resilience check.

    Injects non-numeric strings ("OCHOCIENTOS", "INVALID_FLOAT") into integer/float fields.
    Returns:
        List of raw dictionaries containing invalid type strings.
    """
    return [
        {"code": "MATH101", "credits": "4", "tuition_fee": "1200.50"},
        {"code": "PHYS201", "credits": "OCHOCIENTOS", "tuition_fee": "1500.00"},
        {"code": "CHEM301", "credits": "3", "tuition_fee": "INVALID_FLOAT"},
    ]


def get_invalid_rules_raw_data() -> List[Dict[str, Any]]:
    """ESC-04: Business rule violations for SchemaEngine rule testing.

    Injects negative credits and invalid date ranges.
    Returns:
        List of raw dictionaries violating semantic rules.
    """
    return [
        {"code": "MATH101", "credits": 4, "start_date": "2026-01-15", "end_date": "2026-06-30"},
        {"code": "BAD_CREDITS", "credits": -5, "start_date": "2026-01-15", "end_date": "2026-06-30"},
        {"code": "BAD_DATES", "credits": 3, "start_date": "2026-08-01", "end_date": "2026-06-30"},
    ]


def get_orphan_dependencies_nodes() -> List[LoadNode]:
    """ESC-05: Nodes referencing non-existent parent dependencies.

    Returns:
        List of `LoadNode` instances where `ENR_ORPHAN` depends on `COURSE_GHOST_999`.
    """
    course = LoadNode(
        node_id="CUR_REAL_101",
        entity_name="Course",
        payload_reference={"code": "REAL101"},
    )
    enrollment_orphan = LoadNode(
        node_id="ENR_ORPHAN_001",
        entity_name="Enrollment",
        dependencies={"COURSE_GHOST_999"},
        payload_reference={"student_id": "STU_ALEX_889"},
    )
    return [course, enrollment_orphan]


def get_circular_dependency_nodes() -> List[LoadNode]:
    """ESC-06: Artificial circular dependency graph (A -> B -> C -> A).

    Returns:
        List of 3 `LoadNode` objects forming an exact closed cycle.
    """
    node_a = LoadNode("MOD_A", "AcademicModule", dependencies={"MOD_C"}, payload_reference={"name": "Module A"})
    node_b = LoadNode("MOD_B", "AcademicModule", dependencies={"MOD_A"}, payload_reference={"name": "Module B"})
    node_c = LoadNode("MOD_C", "AcademicModule", dependencies={"MOD_B"}, payload_reference={"name": "Module C"})
    return [node_a, node_b, node_c]


def get_simulated_error_nodes() -> List[LoadNode]:
    """ESC-07: Nodes injecting `simulate_error=True` for retry and cascade skip verification.

    Returns:
        List of `LoadNode` instances where the root node fails intentionally, triggering skips in children.
    """
    root = LoadNode(
        node_id="ROOT_FAIL_001",
        entity_name="CoreConfig",
        payload_reference={"simulate_error": True, "error_message": "Deadlock transaccional simulado en raíz"},
    )
    child_1 = LoadNode(
        node_id="CHILD_SKIP_001",
        entity_name="SubConfig",
        dependencies={"ROOT_FAIL_001"},
        payload_reference={"setting": "alpha"},
    )
    child_2 = LoadNode(
        node_id="CHILD_SKIP_002",
        entity_name="SubConfig",
        dependencies={"CHILD_SKIP_001"},
        payload_reference={"setting": "beta"},
    )
    return [root, child_1, child_2]


def generate_massive_stress_nodes(num_rows: int = 10000, depth: int = 15) -> List[LoadNode]:
    """ESC-09: Massive synthetic dataset generator for performance and DAG stress testing.

    Generates `num_rows` interconnected nodes distributed across `depth` topological levels
    to verify linear graph traversal ($O(V+E)$) without recursion overflow (`RecursionError`).

    Args:
        num_rows: Total number of nodes to generate.
        depth: Number of topological dependency levels.

    Returns:
        List of interconnected `LoadNode` objects.
    """
    nodes: List[LoadNode] = []
    nodes_per_level = max(1, num_rows // depth)

    for level in range(depth):
        for idx in range(nodes_per_level):
            if len(nodes) >= num_rows:
                break
            node_id = f"NODE_L{level}_I{idx}"
            deps = set()
            if level > 0:
                # Depend on the corresponding index (or 0) of the previous level
                parent_idx = min(idx, nodes_per_level - 1)
                deps.add(f"NODE_L{level-1}_I{parent_idx}")

            node = LoadNode(
                node_id=node_id,
                entity_name="StressEntity",
                dependencies=deps,
                payload_reference={"level": level, "index": idx, "value": f"payload_{node_id}"},
            )
            nodes.append(node)

    # If rounding left remaining rows, attach them to the last level
    while len(nodes) < num_rows:
        idx = len(nodes)
        node_id = f"NODE_EXTRA_{idx}"
        node = LoadNode(
            node_id=node_id,
            entity_name="StressEntity",
            dependencies={f"NODE_L0_I0"},
            payload_reference={"extra": True},
        )
        nodes.append(node)

    return nodes


__all__ = [
    "get_happy_path_nodes",
    "get_missing_columns_raw_data",
    "get_invalid_casting_raw_data",
    "get_invalid_rules_raw_data",
    "get_orphan_dependencies_nodes",
    "get_circular_dependency_nodes",
    "get_simulated_error_nodes",
    "generate_massive_stress_nodes",
]
