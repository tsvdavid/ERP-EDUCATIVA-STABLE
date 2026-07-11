# apps/data_engine/components/execution/base.py
"""Abstract contracts for the MAC Execution Engine & Load Execution Framework.

Defines interfaces for:
- ``BaseStepExecutor``: Contract for executing an individual `ExecutionStep`.
- ``BaseExecutionStrategy``: Contract for coordinating the step-by-step traversal of a `LoadPlan`.
- ``BaseExecutionEventListener``: Contract for observing lifecycle transitions and events.
- ``BaseExecutionEngine``: Base component adapter for Layer 11 pipeline components.
"""

from abc import ABC, abstractmethod

from apps.data_engine.components.base import BaseComponent, component_name
from .models import ExecutionContext, ExecutionEvent, ExecutionReport, ExecutionResult, ExecutionStep


class BaseStepExecutor(ABC):
    """Abstract contract for executing an individual `ExecutionStep`."""

    @abstractmethod
    def execute_step(
        self, step: ExecutionStep, exec_context: ExecutionContext
    ) -> ExecutionResult:
        """Execute a single unit of work associated with a `LoadNode`.

        Args:
            step: The `ExecutionStep` instance containing node and attempt details.
            exec_context: The shared in-memory `ExecutionContext`.

        Returns:
            Consolidated `ExecutionResult` describing step success, output, and duration.
        """
        raise NotImplementedError  # pragma: no cover


class BaseExecutionStrategy(ABC):
    """Abstract contract for orchestrating plan traversal across execution groups."""

    @abstractmethod
    def execute_plan(
        self, exec_context: ExecutionContext, executor: BaseStepExecutor
    ) -> ExecutionReport:
        """Traverse the `LoadPlan` in `exec_context` using `executor` for each step.

        Args:
            exec_context: The execution context containing the plan and shared progress.
            executor: The step executor instance to invoke for each node.

        Returns:
            Consolidated `ExecutionReport` encapsulating all step outcomes and metrics.
        """
        raise NotImplementedError  # pragma: no cover


class BaseExecutionEventListener(ABC):
    """Abstract contract for observing lifecycle events emitted during plan execution."""

    @abstractmethod
    def on_event(self, event: ExecutionEvent) -> None:
        """Handle a newly emitted `ExecutionEvent`.

        Args:
            event: The `ExecutionEvent` instance.
        """
        raise NotImplementedError  # pragma: no cover


class BaseExecutionEngine(BaseComponent, ABC):
    """Abstract base for all execution engine components within MAC.

    Subclasses must implement ``execute(self, context)`` and expose a
    ``component_type`` attribute with the value ``"execution_engine"``.
    """

    component_type: str = "execution_engine"


__all__ = [
    "BaseStepExecutor",
    "BaseExecutionStrategy",
    "BaseExecutionEventListener",
    "BaseExecutionEngine",
    "component_name",
]
