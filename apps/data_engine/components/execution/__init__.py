# apps/data_engine/components/execution/__init__.py
"""MAC Execution Engine & Load Execution Framework (TAREA 17).

Provides entities, abstract contracts, execution strategies, simulated executors,
and pipeline adapters for executing topological load plans without ORM coupling:

- Entities: ``ExecutionState``, ``ExecutionEvent``, ``ExecutionStep``,
            ``ExecutionResult``, ``ExecutionMetrics``, ``ExecutionReport``, ``ExecutionContext``
- Contracts: ``BaseStepExecutor``, ``BaseExecutionStrategy``,
             ``BaseExecutionEventListener``, ``BaseExecutionEngine``
- Executors: ``DryRunStepExecutor``
- Strategies: ``SequentialExecutionStrategy``
- Component: ``ExecutionEngineComponent``
"""

from .base import (
    BaseExecutionEngine,
    BaseExecutionEventListener,
    BaseExecutionStrategy,
    BaseStepExecutor,
)
from .component import ExecutionEngineComponent
from .executor import DryRunStepExecutor
from .models import (
    ExecutionContext,
    ExecutionEvent,
    ExecutionMetrics,
    ExecutionReport,
    ExecutionResult,
    ExecutionState,
    ExecutionStep,
)
from .strategies import SequentialExecutionStrategy

__all__ = [
    "ExecutionState",
    "ExecutionEvent",
    "ExecutionStep",
    "ExecutionResult",
    "ExecutionMetrics",
    "ExecutionReport",
    "ExecutionContext",
    "BaseStepExecutor",
    "BaseExecutionStrategy",
    "BaseExecutionEventListener",
    "BaseExecutionEngine",
    "DryRunStepExecutor",
    "SequentialExecutionStrategy",
    "ExecutionEngineComponent",
]
