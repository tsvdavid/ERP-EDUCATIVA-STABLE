# apps/data_engine/components/loaders/graph.py
"""Directed Acyclic Graph (DAG) Engine for MAC dependency resolution.

Provides pure Python graph algorithms without external dependencies (`networkx`, etc.)
operating in O(V + E) time and space complexity:

- ``DirectedGraph``: Encapsulates logical nodes and dependency edges.
- ``topological_sort``: Kahn's algorithm for deterministic topological ordering.
- ``detect_cycles``: Depth-First Search (DFS) with node state tracking (`WHITE`/`GRAY`/`BLACK`)
  to identify and report exact circular dependency paths.
"""

from collections import deque
from typing import Dict, List, Set

from .models import DependencyCycle, LoadNode


class DirectedGraph:
    """Directed Graph implementation tailored for entity loading dependency resolution.

    In this graph, if Node B (`Course`) depends on Node A (`AcademicPeriod`), an edge
    is directed from A to B (`A -> B`), indicating that A must be processed before B.
    """

    def __init__(self):
        self._nodes: Dict[str, LoadNode] = {}
        self._adj: Dict[str, Set[str]] = {}
        self._in_degrees: Dict[str, int] = {}

    def add_node(self, node: LoadNode) -> None:
        """Register a logical node in the graph.

        Args:
            node: The `LoadNode` instance to add.
        """
        if node.node_id not in self._nodes:
            self._nodes[node.node_id] = node
            self._adj[node.node_id] = set()
            self._in_degrees[node.node_id] = 0

    def add_edge(self, from_node_id: str, to_node_id: str) -> None:
        """Add a directed edge from `from_node_id` to `to_node_id`.

        Indicates that `from_node_id` is a prerequisite for `to_node_id`.

        Args:
            from_node_id: Source node identifier (prerequisite).
            to_node_id: Target node identifier (dependent).

        Raises:
            KeyError: If either node ID has not been registered via `add_node`.
        """
        if from_node_id not in self._nodes:
            raise KeyError(f"Source node '{from_node_id}' not registered in graph.")
        if to_node_id not in self._nodes:
            raise KeyError(f"Target node '{to_node_id}' not registered in graph.")

        if to_node_id not in self._adj[from_node_id]:
            self._adj[from_node_id].add(to_node_id)
            self._in_degrees[to_node_id] += 1

    def get_neighbors(self, node_id: str) -> Set[str]:
        """Get all target node IDs directly reachable from `node_id`."""
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' not registered in graph.")
        return set(self._adj.get(node_id, set()))

    def get_in_degree(self, node_id: str) -> int:
        """Get the in-degree (number of prerequisites) for `node_id`."""
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' not registered in graph.")
        return self._in_degrees.get(node_id, 0)

    def get_out_degree(self, node_id: str) -> int:
        """Get the out-degree (number of dependents) for `node_id`."""
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' not registered in graph.")
        return len(self._adj.get(node_id, set()))

    def get_node(self, node_id: str) -> LoadNode:
        """Retrieve the `LoadNode` instance for `node_id`."""
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' not registered in graph.")
        return self._nodes[node_id]

    def get_all_nodes(self) -> List[LoadNode]:
        """Return all registered `LoadNode` instances."""
        return list(self._nodes.values())

    def topological_sort(self) -> List[LoadNode]:
        """Compute a deterministic topological sort of the nodes using Kahn's algorithm.

        Time Complexity: O(V + E)
        Space Complexity: O(V + E)

        Returns:
            List of `LoadNode` sorted such that every prerequisite node precedes its dependents.

        Raises:
            ValueError: If the graph contains one or more cycles.
        """
        # Create a working copy of in-degrees
        in_degree = {u: self._in_degrees[u] for u in self._nodes}

        # Queue of nodes with in-degree 0, sorted by node_id for 100% determinism
        zero_in_degree = deque(sorted([u for u, deg in in_degree.items() if deg == 0]))

        ordered_node_ids = []
        while zero_in_degree:
            u = zero_in_degree.popleft()
            ordered_node_ids.append(u)

            # Check neighbors in deterministic sorted order
            for v in sorted(self._adj[u]):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    zero_in_degree.append(v)

        if len(ordered_node_ids) != len(self._nodes):
            raise ValueError(
                "DirectedGraph contains cycles; cannot perform topological sort."
            )

        return [self._nodes[uid] for uid in ordered_node_ids]

    def detect_cycles(self) -> List[DependencyCycle]:
        """Detect all circular dependency paths using DFS coloring.

        Node states:
            WHITE (0) = Unvisited
            GRAY (1)  = Currently visiting (on DFS recursion stack)
            BLACK (2) = Fully visited

        Time Complexity: O(V + E)
        Space Complexity: O(V)

        Returns:
            List of `DependencyCycle` objects representing distinct cycles found.
        """
        color: Dict[str, int] = {u: 0 for u in self._nodes}
        cycles: List[DependencyCycle] = []
        visited_paths: Set[str] = set()

        for start_node in sorted(self._nodes.keys()):
            if color[start_node] == 0:
                # Stack stores tuples: (node_id, iterator_of_sorted_neighbors)
                stack = [(start_node, iter(sorted(self._adj[start_node])))]
                color[start_node] = 1

                while stack:
                    u, neighbors = stack[-1]
                    try:
                        v = next(neighbors)
                        if color[v] == 1:
                            # Back-edge detected! Reconstruct the cycle path
                            idx = next(
                                i
                                for i, (n_id, _) in enumerate(stack)
                                if n_id == v
                            )
                            path = [n_id for n_id, _ in stack[idx:]] + [v]
                            path_key = "->".join(path)
                            if path_key not in visited_paths:
                                visited_paths.add(path_key)
                                msg = f"Circular dependency detected: {' -> '.join(path)}"
                                cycles.append(
                                    DependencyCycle(cycle_path=path, message=msg)
                                )
                        elif color[v] == 0:
                            color[v] = 1
                            stack.append((v, iter(sorted(self._adj[v]))))
                    except StopIteration:
                        color[u] = 2
                        stack.pop()

        return cycles


__all__ = ["DirectedGraph"]
