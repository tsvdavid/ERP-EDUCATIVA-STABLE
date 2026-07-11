# apps/data_engine/components/loaders/base.py
"""Abstract contracts for the MAC Loader Engine & Dependency Resolution Framework.

Defines interfaces for:
- ``BaseLoadPlanner``: Contract for generating execution plans (`LoadPlan`) from entity nodes.
- ``BaseDependencyResolver``: Contract for resolving dependencies and topological ordering.
- ``BaseLoaderComponent``: Base component adapter for all loader and planning components in MAC.
"""

from abc import ABC, abstractmethod
from typing import Any, List

from apps.data_engine.components.base import BaseComponent, component_name
from .models import LoadNode, LoadPlan


class BaseLoadPlanner(ABC):
    """Abstract contract for generating an execution load plan from logical nodes."""

    @abstractmethod
    def create_plan(self, nodes: List[LoadNode]) -> LoadPlan:
        """Analyze nodes, resolve dependencies, and generate a structured `LoadPlan`.

        Args:
            nodes: List of `LoadNode` instances representing entities to be loaded.

        Returns:
            Consolidated `LoadPlan` with ordered nodes and execution groups.
        """
        raise NotImplementedError  # pragma: no cover


class BaseDependencyResolver(ABC):
    """Abstract contract for dependency resolution and ordering algorithms."""

    @abstractmethod
    def resolve(self, graph: Any) -> List[LoadNode]:
        """Resolve dependencies on a graph structure and return ordered nodes.

        Args:
            graph: A directed graph instance (`DirectedGraph`).

        Returns:
            Topologically sorted list of `LoadNode` items.
        """
        raise NotImplementedError  # pragma: no cover


class BaseLoaderComponent(BaseComponent, ABC):
    """Abstract base for all loader and loader-planning components within MAC.

    Subclasses must implement ``execute(self, context)`` and expose a
    ``component_type`` attribute with the value ``"loader_planner"`` or ``"loader"``.
    """

    component_type: str = "loader_planner"


__all__ = [
    "BaseLoadPlanner",
    "BaseDependencyResolver",
    "BaseLoaderComponent",
    "component_name",
]
