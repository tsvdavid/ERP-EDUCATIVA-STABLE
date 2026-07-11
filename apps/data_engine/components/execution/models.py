# apps/data_engine/components/execution/models.py
"""Domain entities for the MAC Execution Engine & Load Execution Framework.

Defines state structures, execution steps, audit events, and context containers:

- ``ExecutionState``: Enumeration of possible states for execution steps and reports.
- ``ExecutionEvent``: Audit log event tracking lifecycle transitions during plan execution.
- ``ExecutionStep``: Unit of work representing the execution attempt of a single `LoadNode`.
- ``ExecutionResult``: Outcome of executing a step or the overall plan.
- ``ExecutionMetrics``: Quantitative metrics and timing counters for plan execution.
- ``ExecutionReport``: Immutable final manifest consolidating results, events, and metrics.
- ``ExecutionContext``: Shared in-memory state container tracking step progress and outputs.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from apps.data_engine.components.loaders.models import LoadNode, LoadPlan


class ExecutionState(Enum):
    """Enumeration of possible lifecycle states for execution steps and plans."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ABORTED = "ABORTED"


@dataclass
class ExecutionEvent:
    """Audit log event representing a lifecycle transition during execution.

    Attributes:
        event_type: Type identifier (e.g., "START", "STEP_START", "STEP_FINISH", "STEP_ERROR", "STEP_SKIP", "FINISH").
        node_id: Optional ID of the `LoadNode` associated with the event.
        message: Diagnostic description of the transition or error.
        timestamp: UTC ISO-8601 timestamp.
        metadata: Dictionary of extra contextual details.
    """

    event_type: str
    node_id: Optional[str]
    message: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionStep:
    """Represents a discrete unit of work corresponding to a single `LoadNode`.

    Attributes:
        step_id: Unique UUID identifier for this execution attempt.
        node: The `LoadNode` being processed.
        state: Current `ExecutionState`.
        attempts: Number of execution attempts made.
        start_time: UTC ISO-8601 timestamp when step execution started.
        end_time: UTC ISO-8601 timestamp when step execution concluded.
        error_message: Diagnostic error message if the step failed.
        execution_output: Data returned upon successful execution of this step.
    """

    step_id: str
    node: LoadNode
    state: ExecutionState = ExecutionState.PENDING
    attempts: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error_message: Optional[str] = None
    execution_output: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionResult:
    """Result of executing a single `ExecutionStep` or node.

    Attributes:
        success: True if execution completed successfully without errors.
        step_id: ID of the corresponding `ExecutionStep`.
        node_id: ID of the corresponding `LoadNode`.
        state: Final `ExecutionState` (`COMPLETED`, `FAILED`, `SKIPPED`).
        output_data: Dictionary of outputs or reference keys produced by this step.
        error: Diagnostic error message if `success` is False.
        execution_time_ms: Duration of step execution in milliseconds.
    """

    success: bool
    step_id: str
    node_id: str
    state: ExecutionState
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class ExecutionMetrics:
    """Aggregated quantitative metrics for an execution run.

    Attributes:
        total_steps: Total number of steps scheduled for execution.
        completed_steps: Number of steps that reached `COMPLETED` state.
        failed_steps: Number of steps that reached `FAILED` state.
        skipped_steps: Number of steps that reached `SKIPPED` state.
        total_duration_ms: Total elapsed time of the execution run in milliseconds.
        average_step_duration_ms: Mean duration per executed step in milliseconds.
    """

    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    total_duration_ms: float = 0.0
    average_step_duration_ms: float = 0.0


@dataclass
class ExecutionReport:
    """Consolidated final manifest representing the outcome of a plan execution run.

    Attributes:
        report_id: Unique UUID identifier for this report.
        plan_id: ID of the `LoadPlan` that was executed.
        status: Overall `ExecutionState` (`COMPLETED`, `FAILED`, `ABORTED`).
        step_results: List of all individual `ExecutionResult` items.
        metrics: Consolidated `ExecutionMetrics`.
        events: Chronological audit trail of `ExecutionEvent` items emitted during the run.
        start_timestamp: UTC ISO-8601 timestamp when execution initiated.
        end_timestamp: UTC ISO-8601 timestamp when execution completed or aborted.
    """

    report_id: str
    plan_id: str
    status: ExecutionState
    step_results: List[ExecutionResult]
    metrics: ExecutionMetrics
    events: List[ExecutionEvent]
    start_timestamp: str
    end_timestamp: str


@dataclass
class ExecutionContext:
    """Shared in-memory state container utilized across execution steps.

    Tracks progress, intermediate outputs, and events across the execution run
    without writing or coupling to external database persistence.

    Attributes:
        plan: The `LoadPlan` being executed.
        shared_state: Global dictionary for variables shared across all steps.
        step_progress: Mapping of `node_id` to current `ExecutionState`.
        step_outputs: Mapping of `node_id` to intermediate output data dictionaries.
        events: Chronological list of `ExecutionEvent` records.
        is_aborted: Flag indicating whether execution has been globally halted.
    """

    plan: LoadPlan
    shared_state: Dict[str, Any] = field(default_factory=dict)
    step_progress: Dict[str, ExecutionState] = field(default_factory=dict)
    step_outputs: Dict[str, Any] = field(default_factory=dict)
    events: List[ExecutionEvent] = field(default_factory=list)
    is_aborted: bool = False

    def record_event(
        self,
        event_type: str,
        message: str,
        node_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an audit event in the execution context.

        Args:
            event_type: Type identifier (e.g., "STEP_START", "STEP_FINISH").
            message: Descriptive message.
            node_id: Optional node ID.
            metadata: Optional dictionary of extra attributes.
        """
        event = ExecutionEvent(
            event_type=event_type,
            node_id=node_id,
            message=message,
            metadata=metadata or {},
        )
        self.events.append(event)


__all__ = [
    "ExecutionState",
    "ExecutionEvent",
    "ExecutionStep",
    "ExecutionResult",
    "ExecutionMetrics",
    "ExecutionReport",
    "ExecutionContext",
]
