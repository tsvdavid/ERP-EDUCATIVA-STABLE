# apps/data_engine/persistence/executor.py
"""Transactional ORM Step Executor for the Persistence Adapter.

Defines:
- ``DjangoOrmStepExecutor``: Implements ``BaseStepExecutor`` from `apps.data_engine.components.execution.base`
  to safely execute data operations inside Django ORM (`transaction.atomic()` & savepoints).
"""

import time
from typing import Any, Dict

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.data_engine.components.execution.base import BaseStepExecutor
from apps.data_engine.components.execution.models import (
    ExecutionContext,
    ExecutionResult,
    ExecutionState,
    ExecutionStep,
)
from .adapters import RepositoryResolver
from .models import PersistenceContext


class DjangoOrmStepExecutor(BaseStepExecutor):
    """Executes `ExecutionStep` items by persisting them to Django ORM inside atomic savepoints.

    Catches all ORM-related exceptions (`IntegrityError`, `ValidationError`, `ProtectedError`)
    and converts them cleanly to `ExecutionResult(success=False, state=FAILED)` without leaking
    exceptions or corrupting upper-level transactions.
    """

    def execute_step(
        self, step: ExecutionStep, exec_context: ExecutionContext
    ) -> ExecutionResult:
        start_time = time.perf_counter()
        node = step.node
        payload_raw = getattr(node, "payload", None)
        if payload_raw is None:
            payload_raw = getattr(node, "payload_reference", {})
        payload = payload_raw.copy() if isinstance(payload_raw, dict) else {}

        # 1. Check if step is already skipped or completed
        if step.state in (ExecutionState.SKIPPED, ExecutionState.COMPLETED, ExecutionState.FAILED):
            return ExecutionResult(
                success=(step.state == ExecutionState.COMPLETED),
                step_id=step.step_id,
                node_id=node.node_id,
                state=step.state,
                output_data=step.execution_output or {},
                error=step.error_message,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )

        # 2. Extract multi-tenant ID from context or payload
        shared = exec_context.shared_state
        metadata = shared.get("metadata", {}) if isinstance(shared, dict) else {}
        tenant_id = (
            shared.get("institution_id")
            or metadata.get("institution_id")
            or payload.get("institution_id")
            or "default"
        )

        is_dry_run = shared.get("is_dry_run", False) if isinstance(shared, dict) else False

        persistence_ctx = PersistenceContext(
            tenant_id=str(tenant_id),
            resolved_dependencies=exec_context.step_outputs,
            is_dry_run=is_dry_run,
        )

        # 3. Check for simulated error flag (for testing resilience without breaking real DB)
        if payload.get("simulate_error") is True:
            err_msg = "[SimulatedError] Step failed due to simulate_error flag in payload"
            exec_context.record_event(
                "STEP_ERROR",
                message=err_msg,
                node_id=node.node_id,
            )
            return ExecutionResult(
                success=False,
                step_id=step.step_id,
                node_id=node.node_id,
                state=ExecutionState.FAILED,
                error=err_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )

        # 4. Resolve repository for entity_name
        try:
            repository = RepositoryResolver.resolve_for_node(node)
        except (KeyError, TypeError) as exc:
            err_msg = f"[RepositoryResolutionError] {exc}"
            exec_context.record_event(
                "STEP_ERROR",
                message=err_msg,
                node_id=node.node_id,
            )
            return ExecutionResult(
                success=False,
                step_id=step.step_id,
                node_id=node.node_id,
                state=ExecutionState.FAILED,
                error=err_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )

        # 5. Execute persistence within atomic savepoint boundary
        exec_context.record_event(
            "STEP_START",
            message=f"Starting ORM persistence step for node {node.node_id} ({node.entity_name})",
            node_id=node.node_id,
        )

        try:
            with transaction.atomic():
                savepoint = transaction.savepoint()

                try:
                    # Validate domain constraints
                    val_errors = repository.validate_constraints(payload, persistence_ctx)
                    if val_errors:
                        transaction.savepoint_rollback(savepoint)
                        err_str = "[ValidationError] " + "; ".join(val_errors)
                        exec_context.record_event(
                            "STEP_ERROR",
                            message=err_str,
                            node_id=node.node_id,
                        )
                        return ExecutionResult(
                            success=False,
                            step_id=step.step_id,
                            node_id=node.node_id,
                            state=ExecutionState.FAILED,
                            error=err_str,
                            execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
                        )

                    # Find existing or create/update
                    existing = repository.find_existing(payload, persistence_ctx)
                    if existing is not None:
                        entity_res = repository.update(existing, payload, persistence_ctx)
                    else:
                        entity_res = repository.create(payload, persistence_ctx)

                    # Check entity persistence result status
                    if not entity_res.success:
                        transaction.savepoint_rollback(savepoint)
                        err_str = "[PersistenceError] " + "; ".join(entity_res.errors)
                        exec_context.record_event(
                            "STEP_ERROR",
                            message=err_str,
                            node_id=node.node_id,
                        )
                        return ExecutionResult(
                            success=False,
                            step_id=step.step_id,
                            node_id=node.node_id,
                            state=ExecutionState.FAILED,
                            error=err_str,
                            execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
                        )

                    # If dry run or rollback requested, rollback savepoint
                    if is_dry_run:
                        transaction.savepoint_rollback(savepoint)
                    else:
                        transaction.savepoint_commit(savepoint)

                    output_data: Dict[str, Any] = payload.copy()
                    if entity_res.orm_id:
                        output_data["orm_id"] = entity_res.orm_id
                    output_data["entity_result"] = entity_res

                    exec_context.record_event(
                        "STEP_FINISH",
                        message=f"Completed ORM persistence for node {node.node_id} (ORM ID: {entity_res.orm_id})",
                        node_id=node.node_id,
                    )

                    return ExecutionResult(
                        success=True,
                        step_id=step.step_id,
                        node_id=node.node_id,
                        state=ExecutionState.COMPLETED,
                        output_data=output_data,
                        execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
                    )

                except (IntegrityError, ValidationError, ProtectedError) as exc:
                    transaction.savepoint_rollback(savepoint)
                    err_msg = f"[{exc.__class__.__name__}] {exc}"
                    exec_context.record_event(
                        "STEP_ERROR",
                        message=err_msg,
                        node_id=node.node_id,
                    )
                    return ExecutionResult(
                        success=False,
                        step_id=step.step_id,
                        node_id=node.node_id,
                        state=ExecutionState.FAILED,
                        error=err_msg,
                        execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
                    )

        except Exception as exc:  # Catch any outer unexpected DB driver error
            err_msg = f"[{exc.__class__.__name__}] {exc}"
            exec_context.record_event(
                "STEP_ERROR",
                message=err_msg,
                node_id=node.node_id,
            )
            return ExecutionResult(
                success=False,
                step_id=step.step_id,
                node_id=node.node_id,
                state=ExecutionState.FAILED,
                error=err_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )


__all__ = [
    "DjangoOrmStepExecutor",
]
