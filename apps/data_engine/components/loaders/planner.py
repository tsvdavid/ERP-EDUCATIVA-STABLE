# apps/data_engine/components/loaders/planner.py
"""Dependency Planner for MAC Loader Engine & Dependency Resolution Framework.

Implements the central planning logic that converts lists of logical entity nodes
into execution plans (`LoadPlan`):

- ``DependencyPlanner``: Builds the `DirectedGraph`, inspects for circular dependencies,
  performs topological sorting, and computes parallel execution groups by level.
"""

from typing import Dict, List

from .base import BaseDependencyResolver, BaseLoadPlanner
from .graph import DirectedGraph
from .models import LoadNode, LoadPlan


class DependencyPlanner(BaseLoadPlanner, BaseDependencyResolver):
    """Central dependency planner for orchestrating entity loading order.

    Converts entity nodes into a directed graph, verifies acyclic structure,
    determines deterministic execution sequence, and groups nodes by depth level.
    """

    def build_graph(self, nodes: List[LoadNode]) -> DirectedGraph:
        """Construct a `DirectedGraph` from a list of `LoadNode` items.

        Args:
            nodes: List of registered `LoadNode` instances.

        Returns:
            Populated `DirectedGraph` with nodes and prerequisite edges.

        Raises:
            KeyError: If a node declares a dependency `node_id` that is not present in `nodes`.
        """
        graph = DirectedGraph()
        for node in nodes:
            graph.add_node(node)

        for node in nodes:
            for dep_id in sorted(node.dependencies):
                # Edge from prerequisite (dep_id) to dependent (node.node_id)
                graph.add_edge(dep_id, node.node_id)

        return graph

    def resolve(self, graph: DirectedGraph) -> List[LoadNode]:
        """Execute topological sort on `graph` to resolve dependency ordering.

        Args:
            graph: Populated `DirectedGraph`.

        Returns:
            Deterministic ordered list of `LoadNode` items.

        Raises:
            ValueError: If `graph` contains circular dependencies.
        """
        return graph.topological_sort()

    def create_execution_groups(
        self, graph: DirectedGraph, ordered_nodes: List[LoadNode]
    ) -> List[List[LoadNode]]:
        """Group `ordered_nodes` into topological depth levels for parallel execution.

        Level 0: Nodes with no prerequisites (or whose prerequisites are outside this plan).
        Level K: Nodes whose maximum prerequisite depth level is K - 1.

        Args:
            graph: The underlying `DirectedGraph`.
            ordered_nodes: Topologically sorted list of `LoadNode` instances.

        Returns:
            List of lists where each sublist contains `LoadNode` items at that execution level.
        """
        if not ordered_nodes:
            return []

        node_levels: Dict[str, int] = {}
        for node in ordered_nodes:
            if not node.dependencies:
                node_levels[node.node_id] = 0
            else:
                max_dep_level = -1
                for dep_id in node.dependencies:
                    if dep_id in node_levels:
                        max_dep_level = max(max_dep_level, node_levels[dep_id])
                node_levels[node.node_id] = max_dep_level + 1

        max_level = max(node_levels.values(), default=0)
        groups: List[List[LoadNode]] = [[] for _ in range(max_level + 1)]

        for node in ordered_nodes:
            level = node_levels[node.node_id]
            groups[level].append(node)

        return groups

    def create_plan(self, nodes: List[LoadNode]) -> LoadPlan:
        """Analyze `nodes`, verify graph integrity, and produce an immutable `LoadPlan`.

        If circular dependencies are detected, returns a plan with `has_cycles=True`
        and populated `cycles`, without throwing an exception, allowing safe inspection.

        Args:
            nodes: List of `LoadNode` items representing entities to be planned.

        Returns:
            Consolidated `LoadPlan`.
        """
        graph = self.build_graph(nodes)
        cycles = graph.detect_cycles()

        if cycles:
            return LoadPlan(
                ordered_nodes=[],
                execution_groups=[],
                has_cycles=True,
                total_nodes=len(nodes),
                cycles=cycles,
            )

        ordered_nodes = self.resolve(graph)
        execution_groups = self.create_execution_groups(graph, ordered_nodes)

        return LoadPlan(
            ordered_nodes=ordered_nodes,
            execution_groups=execution_groups,
            has_cycles=False,
            total_nodes=len(nodes),
            cycles=[],
        )


__all__ = ["DependencyPlanner"]
