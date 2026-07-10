# apps/data_engine/core/orchestrator.py
"""Core orchestrator for the MAC (Motor de Análisis y Carga) subsystem.

The orchestrator receives an *operation* name and a *context* dict and delegates the
work to a registered component. It also supports executing a pipeline of
components when a list of component names is provided.
"""

from typing import List, Optional

from .registry import MacRegistry
from .exceptions import ComponentNotFoundError, ComponentExecutionError


class MacOrchestrator:
    """Orchestrator that looks up components and calls their ``execute`` method.

    Parameters
    ----------
    registry: MacRegistry, optional
        Registry instance to use. If omitted a global singleton registry is used.
    """

    def __init__(self, registry: MacRegistry | None = None):
        self._registry = registry or MacRegistry.global_registry()

    def execute(
        self,
        operation: str,
        context: dict | None = None,
        components: Optional[List[str]] = None,
    ):
        """Execute a single operation or a pipeline of components.

        If *components* is provided, *operation* is ignored and the orchestrator
        will sequentially invoke each registered component name, passing the
        (potentially mutated) *context* from one to the next. The result of the
        last component is returned.
        """
        context = context or {}
        if components:
            for name in components:
                try:
                    component = self._registry.get(name)
                except ComponentNotFoundError as exc:
                    raise ComponentNotFoundError(
                        f"Component '{name}' not registered in pipeline"
                    ) from exc
                try:
                    result = component.execute(context)
                except Exception as exc:
                    raise ComponentExecutionError(
                        f"Error executing component '{name}': {exc}"
                    ) from exc
                # Merge dict results into the context for downstream components.
                if isinstance(result, dict):
                    context.update(result)
                else:
                    context = result
            return context
        else:
            try:
                component = self._registry.get(operation)
            except ComponentNotFoundError as exc:
                raise ComponentNotFoundError(
                    f"Operation '{operation}' not registered"
                ) from exc
            return component.execute(context)
