# apps/data_engine/components/execution/strategies.py
"""Execution strategies for the MAC Execution Engine & Load Execution Framework.

Defines:
- ``SequentialExecutionStrategy``: Traverses topological execution groups sequentially,
  validates node dependency state before step dispatch, handles cascading skips upon
  prerequisite failures, and generates an audit-ready `ExecutionReport`.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import List

from .base import BaseExecutionStrategy, BaseStepExecutor
from .models import (
    ExecutionContext,
    ExecutionMetrics,
    ExecutionReport,
    ExecutionResult,
    ExecutionState,
    ExecutionStep,
)


class SequentialExecutionStrategy(BaseExecutionStrategy):
    """Executes a `LoadPlan` sequentially level-by-level across topological groups.

    Enforces deterministic prerequisite checking: if any dependency of a `LoadNode`
    did not complete successfully (`FAILED` or `SKIPPED`), the dependent step is
    automatically skipped (`SKIPPED`) with an audit event, preserving pipeline stability.
    """

    def execute_plan(
        self, exec_context: ExecutionContext, executor: BaseStepExecutor
    ) -> ExecutionReport:
        """Execute the `LoadPlan` contained in `exec_context`.

        Args:
            exec_context: The execution context tracking progress and events.
            executor: The step executor instance to run each node.

        Returns:
            Consolidated `ExecutionReport` detailing step outcomes and timing metrics.
        """
        start_timestamp = datetime.now(timezone.utc).isoformat()
        start_timer = time.perf_counter()

        plan = exec_context.plan
        exec_context.record_event(
            "START", f"Starting execution of plan {plan.plan_id}"
        )

        # Abort immediately if the plan has circular dependencies or is invalid
        if plan.has_cycles:
            exec_context.record_event(
                "FINISH",
                "Plan execution aborted due to detected circular dependencies",
            )
            end_timestamp = datetime.now(timezone.utc).isoformat()
            return ExecutionReport(
                report_id=str(uuid.uuid4()),
                plan_id=plan.plan_id,
                status=ExecutionState.FAILED,
                step_results=[],
                metrics=ExecutionMetrics(),
                events=list(exec_context.events),
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
            )

        step_results: List[ExecutionResult] = []
        completed_steps = 0
        failed_steps = 0
        skipped_steps = 0

        # Traverse groups ordered by topological depth (Level 0, Level 1, ...)
        for level_idx, group in enumerate(plan.execution_groups):
            if exec_context.is_aborted:
                exec_context.record_event(
                    "FINISH", f"Execution aborted before group level {level_idx}"
                )
                break

            for node in group:
                if exec_context.is_aborted:
                    exec_context.record_event(
                        "FINISH",
                        f"Execution aborted before node {node.node_id}",
                    )
                    break

                step_id = str(uuid.uuid4())

                # Check all prerequisite dependencies of this node
                missing_or_failed = [
                    dep_id
                    for dep_id in sorted(node.dependencies)
                    if exec_context.step_progress.get(dep_id) != ExecutionState.COMPLETED
                ]

                if missing_or_failed:
                    msg = (
                        "Prerequisite nodes failed or skipped: "
                        + ", ".join(missing_or_failed)
                    )
                    exec_context.step_progress[node.node_id] = ExecutionState.SKIPPED
                    exec_context.record_event(
                        "STEP_SKIP", msg, node_id=node.node_id
                    )
                    skipped_steps += 1
                    step_results.append(
                        ExecutionResult(
                            success=False,
                            step_id=step_id,
                            node_id=node.node_id,
                            state=ExecutionState.SKIPPED,
                            error=msg,
                            execution_time_ms=0.0,
                        )
                    )
                    continue

                # Prereqs are satisfied; dispatch step execution
                step = ExecutionStep(
                    step_id=step_id,
                    node=node,
                    state=ExecutionState.RUNNING,
                    attempts=1,
                    start_time=datetime.now(timezone.utc).isoformat(),
                )
                exec_context.step_progress[node.node_id] = ExecutionState.RUNNING
                exec_context.record_event(
                    "STEP_START",
                    f"Starting step {step_id} for node {node.node_id}",
                    node_id=node.node_id,
                )

                try:
                    result = executor.execute_step(step, exec_context)
                except Exception as exc:
                    result = ExecutionResult(
                        success=False,
                        step_id=step_id,
                        node_id=node.node_id,
                        state=ExecutionState.FAILED,
                        error=str(exc),
                        execution_time_ms=0.0,
                    )

                if result.success and result.state == ExecutionState.COMPLETED:
                    exec_context.step_progress[node.node_id] = ExecutionState.COMPLETED
                    exec_context.step_outputs[node.node_id] = result.output_data
                    completed_steps += 1
                    exec_context.record_event(
                        "STEP_FINISH",
                        f"Completed node {node.node_id} successfully",
                        node_id=node.node_id,
                    )
                else:
                    exec_context.step_progress[node.node_id] = result.state
                    if result.state == ExecutionState.FAILED:
                        failed_steps += 1
                        exec_context.record_event(
                            "STEP_ERROR",
                            f"Failed node {node.node_id}: {result.error}",
                            node_id=node.node_id,
                        )
                    elif result.state == ExecutionState.SKIPPED:
                        skipped_steps += 1
                        exec_context.record_event(
                            "STEP_SKIP",
                            f"Skipped node {node.node_id}: {result.error}",
                            node_id=node.node_id,
                        )

                step_results.append(result)

        # Calculate metrics
        total_duration = (time.perf_counter() - start_timer) * 1000.0
        total_steps = completed_steps + failed_steps + skipped_steps
        avg_duration = (
            total_duration / total_steps if total_steps > 0 else 0.0
        )

        metrics = ExecutionMetrics(
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            total_duration_ms=total_duration,
            average_step_duration_ms=avg_duration,
        )

        # Determine overall execution status
        if exec_context.is_aborted:
            overall_status = ExecutionState.ABORTED
        elif failed_steps > 0 or skipped_steps > 0:
            overall_status = ExecutionState.FAILED
        else:
            overall_status = ExecutionState.COMPLETED

        exec_context.record_event(
            "FINISH", f"Execution concluded with status {overall_status.value}"
        )
        end_timestamp = datetime.now(timezone.utc).isoformat()

        return ExecutionReport(
            report_id=str(uuid.uuid4()),
            plan_id=plan.plan_id,
            status=overall_status,
            step_results=step_results,
            metrics=metrics,
            events=list(exec_context.events),
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )


__all__ = ["SequentialExecutionStrategy"]
