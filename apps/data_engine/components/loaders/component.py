# apps/data_engine/components/loaders/component.py
"""Pipeline Adapter for MAC Loader Engine & Dependency Resolution Framework.

Defines:
- ``LoaderPlanningComponent``: Layer 10 pipeline component that inspects entity nodes,
  invokes the `DependencyPlanner`, and attaches a `LoadPlan` to `context["metadata"]["load_plan"]`.
"""

from typing import Any, Dict, List, Optional

from .base import BaseLoadPlanner, BaseLoaderComponent
from .models import LoadNode
from .planner import DependencyPlanner


class LoaderPlanningComponent(BaseLoaderComponent):
    """Orchestrates entity dependency resolution and generates an execution `LoadPlan`.

    Sits at Layer 10 of the MAC pipeline. It does not perform actual database insertions;
    instead, it calculates the topological loading schedule and detects circular dependencies
    to prepare for future transactional loaders.
    """

    def __init__(self, planner: Optional[BaseLoadPlanner] = None):
        """Initialize the LoaderPlanningComponent.

        Args:
            planner: Optional `BaseLoadPlanner` instance. Defaults to `DependencyPlanner`.
        """
        if planner is not None and not isinstance(planner, BaseLoadPlanner):
            raise TypeError("planner must implement BaseLoadPlanner contract.")
        self._planner = planner or DependencyPlanner()

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute dependency planning and inject `load_plan` into context metadata.

        Args:
            context: The pipeline execution context (`MacContext`).

        Returns:
            The enriched context with `metadata["load_plan"]` attached.

        Raises:
            TypeError: If `context` is not a dictionary.
        """
        if not isinstance(context, dict):
            raise TypeError("Context must be a dictionary.")

        metadata = context.setdefault("metadata", {})

        # Extract pre-registered load_nodes or infer a default node representing the payload
        nodes: List[LoadNode] = metadata.get("load_nodes")
        if not nodes or not isinstance(nodes, list):
            entity_name = metadata.get("target_entity", "UnknownEntity")
            nodes = [
                LoadNode(
                    node_id=f"node_{entity_name}",
                    entity_name=entity_name,
                    payload_reference=context.get("payload"),
                )
            ]

        # Generate LoadPlan
        load_plan = self._planner.create_plan(nodes)
        metadata["load_plan"] = load_plan

        return context


__all__ = ["LoaderPlanningComponent"]
