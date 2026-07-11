# apps/data_engine/components/execution/executor.py
"""Dry-Run Step Executor for the MAC Execution Engine & Load Execution Framework.

Defines:
- ``DryRunStepExecutor``: Concrete implementation of `BaseStepExecutor` that processes
  steps in memory, validates references, and simulates outcomes without database writes.
"""

import time
from typing import Any, Dict

from .base import BaseStepExecutor
from .models import ExecutionContext, ExecutionResult, ExecutionState, ExecutionStep


class DryRunStepExecutor(BaseStepExecutor):
    """Simulated step executor for dry-run execution and pipeline verification.

    Processes `LoadNode` steps entirely in memory without interacting with Django ORM
    or database persistence. Supports error simulation for testing retry/skip policies.
    """

    def execute_step(
        self, step: ExecutionStep, exec_context: ExecutionContext
    ) -> ExecutionResult:
        """Execute a step in dry-run mode.

        Args:
            step: The `ExecutionStep` instance to execute.
            exec_context: The shared in-memory `ExecutionContext`.

        Returns:
            An `ExecutionResult` representing the simulated outcome.
        """
        start_counter = time.perf_counter()

        node = step.node
        payload = node.payload_reference

        # Check for simulated error flag in payload for testing failure behavior
        if isinstance(payload, dict) and payload.get("simulate_error"):
            error_msg = str(
                payload.get("error_message", f"Simulated execution failure on node {node.node_id}")
            )
            elapsed_ms = (time.perf_counter() - start_counter) * 1000.0
            return ExecutionResult(
                success=False,
                step_id=step.step_id,
                node_id=node.node_id,
                state=ExecutionState.FAILED,
                error=error_msg,
                execution_time_ms=elapsed_ms,
            )

        # Simulate successful processing and build reference output
        output_data: Dict[str, Any] = {
            "node_id": node.node_id,
            "entity_name": node.entity_name,
            "simulated_id": f"sim_{node.node_id}",
            "status": "SUCCESS",
        }

        # If payload is a dict, preserve key identifiers or attributes
        if isinstance(payload, dict):
            for k, v in payload.items():
                if k not in output_data and isinstance(v, (str, int, float, bool)):
                    output_data[k] = v

        elapsed_ms = (time.perf_counter() - start_counter) * 1000.0
        return ExecutionResult(
            success=True,
            step_id=step.step_id,
            node_id=node.node_id,
            state=ExecutionState.COMPLETED,
            output_data=output_data,
            execution_time_ms=elapsed_ms,
        )


__all__ = ["DryRunStepExecutor"]
