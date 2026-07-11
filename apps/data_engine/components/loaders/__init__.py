# apps/data_engine/components/loaders/__init__.py
"""MAC Loader Engine & Dependency Resolution Framework (TAREA 16).

Provides entities, graph engine, topological planners, and pipeline components
for resolving dependency order across entity loading workflows without ORM coupling:

- Entities: ``LoadNode``, ``DependencyCycle``, ``LoadPlan``
- Contracts: ``BaseLoadPlanner``, ``BaseDependencyResolver``, ``BaseLoaderComponent``
- Graph Engine: ``DirectedGraph``
- Planners: ``DependencyPlanner``
- Component: ``LoaderPlanningComponent``
"""

from .base import BaseDependencyResolver, BaseLoaderComponent, BaseLoadPlanner
from .component import LoaderPlanningComponent
from .graph import DirectedGraph
from .models import DependencyCycle, LoadNode, LoadPlan
from .planner import DependencyPlanner

__all__ = [
    "LoadNode",
    "DependencyCycle",
    "LoadPlan",
    "BaseLoadPlanner",
    "BaseDependencyResolver",
    "BaseLoaderComponent",
    "DirectedGraph",
    "DependencyPlanner",
    "LoaderPlanningComponent",
]
