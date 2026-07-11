# apps/data_engine/components/execution/component.py
"""Pipeline Adapter for MAC Execution Engine & Load Execution Framework.

Defines:
- ``ExecutionEngineComponent``: Layer 11 pipeline component that consumes the `LoadPlan`
  from context metadata, executes steps via strategies and executors without ORM coupling,
  and attaches the resulting `ExecutionReport` to `context["metadata"]["execution_report"]`.
"""

from typing import Any, Dict, Optional

from apps.data_engine.components.loaders.models import LoadNode, LoadPlan
from apps.data_engine.components.loaders.planner import DependencyPlanner
from .base import BaseExecutionEngine, BaseExecutionStrategy, BaseStepExecutor
from .executor import DryRunStepExecutor
from .models import ExecutionContext
from .strategies import SequentialExecutionStrategy


class ExecutionEngineComponent(BaseExecutionEngine):
    """Orchestrates plan execution and generates an `ExecutionReport`.

    Sits at Layer 11 of the MAC pipeline immediately following `LoaderPlanningComponent` (Layer 10).
    It executes the `LoadPlan` step-by-step using pure domain models and simulated executors,
    ensuring 100% decoupling from Django ORM while verifying full state and retry logic.
    """

    def __init__(
        self,
        strategy: Optional[BaseExecutionStrategy] = None,
        executor: Optional[BaseStepExecutor] = None,
    ):
        """Initialize the ExecutionEngineComponent.

        Args:
            strategy: Optional `BaseExecutionStrategy`. Defaults to `SequentialExecutionStrategy`.
            executor: Optional `BaseStepExecutor`. Defaults to `DryRunStepExecutor`.
        """
        if strategy is not None and not isinstance(strategy, BaseExecutionStrategy):
            raise TypeError("strategy must implement BaseExecutionStrategy contract.")
        if executor is not None and not isinstance(executor, BaseStepExecutor):
            raise TypeError("executor must implement BaseStepExecutor contract.")

        self._strategy = strategy or SequentialExecutionStrategy()
        self._executor = executor or DryRunStepExecutor()

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the `LoadPlan` and inject `execution_report` into context metadata.

        Args:
            context: The pipeline execution context (`MacContext`).

        Returns:
            The enriched context with `metadata["execution_report"]` attached.

        Raises:
            TypeError: If `context` is not a dictionary.
        """
        if not isinstance(context, dict):
            raise TypeError("Context must be a dictionary.")

        metadata = context.setdefault("metadata", {})
        load_plan = metadata.get("load_plan")

        # If load_plan is missing or invalid, generate one dynamically from nodes/payload
        if not isinstance(load_plan, LoadPlan):
            nodes = metadata.get("load_nodes")
            if not nodes or not isinstance(nodes, list):
                entity_name = metadata.get("target_entity", "UnknownEntity")
                nodes = [
                    LoadNode(
                        node_id=f"node_{entity_name}",
                        entity_name=entity_name,
                        payload_reference=context.get("payload"),
                    )
                ]
            load_plan = DependencyPlanner().create_plan(nodes)
            metadata["load_plan"] = load_plan

        # Create execution context and execute the plan
        exec_context = ExecutionContext(plan=load_plan)
        report = self._strategy.execute_plan(exec_context, self._executor)

        metadata["execution_report"] = report
        return context


__all__ = ["ExecutionEngineComponent"]
