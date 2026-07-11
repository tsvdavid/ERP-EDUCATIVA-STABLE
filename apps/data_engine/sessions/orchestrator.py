# apps/data_engine/sessions/orchestrator.py
"""Import Workflow Orchestrator.

Coordinates the 10 sequential phases of an import session across the MAC pipeline:
Reader -> Parser -> Validation -> Mapping -> Schema & Caster -> Staging ->
Reconciliation -> Loader Planning -> Execution -> Persistence Adapter.

Strictly adheres to Clean Architecture and Zero-ORM outside persistence/.
"""

import uuid
from typing import Any, Dict, List, Optional

from apps.data_engine.core.exceptions import ComponentNotFoundError, MacError
from apps.data_engine.core.orchestrator import MacOrchestrator
from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.components.execution.base import BaseStepExecutor, ExecutionContext
from apps.data_engine.components.execution.strategies import SequentialExecutionStrategy

from .base import BaseWorkflowOrchestrator
from .models import ImportSession, SessionReport, SessionState
from .tracker import SessionTracker


class ImportWorkflowOrchestrator(BaseWorkflowOrchestrator):
    """High-level workflow orchestrator managing session state across the 10 MAC layers.

    Parameters
    ----------
    step_executor: Optional[BaseStepExecutor]
        Concrete step executor for Phase 10 (e.g. DjangoOrmStepExecutor). If omitted,
        execution uses dry-run / in-memory step execution.
    registry: Optional[MacRegistry]
        Registry instance for component resolution.
    orchestrator: Optional[MacOrchestrator]
        Core orchestrator instance for executing registered components.
    """

    def __init__(
        self,
        step_executor: Optional[BaseStepExecutor] = None,
        registry: Optional[MacRegistry] = None,
        orchestrator: Optional[MacOrchestrator] = None,
    ):
        if step_executor is not None and not isinstance(step_executor, BaseStepExecutor):
            raise TypeError("step_executor must implement BaseStepExecutor")
        self.step_executor = step_executor
        self.registry = registry or MacRegistry.global_registry()
        self.orchestrator = orchestrator or MacOrchestrator(self.registry)

    def run_workflow(
        self,
        tenant_id: str,
        user_id: str,
        source: Any,
        pipeline_config: Dict[str, Any],
        run_id: Optional[str] = None,
        is_dry_run: bool = False,
    ) -> SessionReport:
        """Execute the full 10-layer import workflow with state tracking and abort cascades."""
        if not tenant_id:
            raise ValueError("tenant_id is required")
        if not user_id:
            raise ValueError("user_id is required")
        if not isinstance(pipeline_config, dict):
            raise TypeError("pipeline_config must be a dictionary")

        session = ImportSession(
            session_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            run_id=run_id or str(uuid.uuid4()),
            state=SessionState.CREATED,
        )
        tracker = SessionTracker(session)

        context: Dict[str, Any] = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "run_id": session.run_id,
            "payload": {},
            "metadata": {
                "source": source,
                "file_path": source if isinstance(source, str) else None,
                "is_dry_run": is_dry_run,
            },
        }

        # Helper to execute a phase cleanly with automatic timing and error catching
        def _run_phase(
            phase_name: str,
            target_state: SessionState,
            component_names: List[str],
            required: bool = True,
        ) -> bool:
            if not component_names:
                if required:
                    start_t = tracker.start_phase(phase_name, target_state)
                    tracker.end_phase(phase_name, start_t, False, 0, 0, [f"No components specified for {phase_name}"])
                    tracker.abort_session(f"Missing required configuration for {phase_name}", SessionState.FAILED)
                    return False
                return True

            start_t = tracker.start_phase(phase_name, target_state)
            input_cnt = _get_record_count(context)
            try:
                for name in component_names:
                    comp = self.registry.get(name)
                    res = comp.execute(context)
                    if isinstance(res, dict):
                        context.update(res)
                    else:
                        context["last_output"] = res
            except Exception as exc:
                output_cnt = _get_record_count(context)
                tracker.end_phase(phase_name, start_t, False, input_cnt, output_cnt, [str(exc)])
                tracker.abort_session(f"Phase '{phase_name}' failed: {exc}", SessionState.FAILED)
                return False

            # Check if any phase result or component reported failure in context metadata/results
            phase_errors: List[str] = []
            if phase_name == "Reconciliation" and context.get("reconciliation_manifest"):
                manifest = context["reconciliation_manifest"]
                if getattr(manifest, "status", None) and str(getattr(manifest, "status", "")).upper() == "VIOLATION":
                    phase_errors.append("Reconciliation conservation law violation detected")

            if phase_name == "Loader Planning" and context.get("load_plan"):
                plan = context["load_plan"]
                if getattr(plan, "has_cycles", False):
                    phase_errors.append("Cyclic dependency detected in load plan")

            output_cnt = _get_record_count(context)
            if phase_errors:
                tracker.end_phase(phase_name, start_t, False, input_cnt, output_cnt, phase_errors)
                tracker.abort_session(f"Phase '{phase_name}' failed: {phase_errors[0]}", SessionState.FAILED)
                return False

            tracker.end_phase(phase_name, start_t, True, input_cnt, output_cnt)
            return True

        # --- Phase 1: Reader ---
        readers = _to_list(pipeline_config.get("reader", []))
        if not _run_phase("Reader", SessionState.INGESTING, readers, required=bool(readers)):
            return tracker.build_report(context)

        # --- Phase 2: Parser ---
        parsers = _to_list(pipeline_config.get("parser", []))
        if not _run_phase("Parser", SessionState.PARSING, parsers, required=bool(parsers)):
            return tracker.build_report(context)

        # --- Phase 3: Validation ---
        validators = _to_list(pipeline_config.get("validators", []))
        if not _run_phase("Validation", SessionState.VALIDATING, validators, required=False):
            return tracker.build_report(context)

        # --- Phase 4: Mapping ---
        mappers = _to_list(pipeline_config.get("mapper", []))
        if not _run_phase("Mapping", SessionState.MAPPING, mappers, required=False):
            return tracker.build_report(context)

        # --- Phase 5: Schema & Caster ---
        casters = _to_list(pipeline_config.get("casters", []))
        if not _run_phase("Schema & Caster", SessionState.STAGING, casters, required=False):
            return tracker.build_report(context)

        # --- Phase 6: Staging ---
        staging = _to_list(pipeline_config.get("staging", []))
        if not _run_phase("Staging", SessionState.STAGING, staging, required=False):
            return tracker.build_report(context)

        # --- Phase 7: Reconciliation ---
        reconciliation = _to_list(pipeline_config.get("reconciliation", []))
        if not _run_phase("Reconciliation", SessionState.RECONCILING, reconciliation, required=False):
            return tracker.build_report(context)

        # --- Phase 8: Loader Planning ---
        loaders = _to_list(pipeline_config.get("loader", []))
        if not _run_phase("Loader Planning", SessionState.PLANNING, loaders, required=False):
            return tracker.build_report(context)

        # --- Phase 9 & 10: Execution & Persistence ---
        # If a load_plan exists or execution component is registered, run execution
        execution_comps = _to_list(pipeline_config.get("execution_engine", []))
        start_t = tracker.start_phase("Execution Engine", SessionState.EXECUTING)
        input_cnt = _get_record_count(context)

        try:
            if execution_comps:
                for name in execution_comps:
                    comp = self.registry.get(name)
                    res = comp.execute(context)
                    if isinstance(res, dict):
                        context.update(res)
            elif context.get("load_plan"):
                # Execute plan directly via strategy if no specific component name given
                plan = context["load_plan"]
                strategy = SequentialExecutionStrategy()
                exec_context = ExecutionContext(
                    plan=plan,
                    shared_state={"institution_id": tenant_id, "tenant_id": tenant_id, "is_dry_run": is_dry_run},
                )
                exec_result = strategy.execute_plan(exec_context, executor=self.step_executor)
                context["execution_result"] = exec_result
                if getattr(exec_result, "failed_steps", 0) > 0:
                    raise MacError(f"Execution failed on {exec_result.failed_steps} steps")
            tracker.end_phase("Execution Engine", start_t, True, input_cnt, input_cnt)
        except Exception as exc:
            tracker.end_phase("Execution Engine", start_t, False, input_cnt, input_cnt, [str(exc)])
            tracker.abort_session(f"Execution phase failed: {exc}", SessionState.FAILED)
            return tracker.build_report(context)

        # --- Phase 10: Persistence Adapter ---
        start_p = tracker.start_phase("Persistence Adapter", SessionState.PERSISTING)
        try:
            if self.step_executor and context.get("load_plan") and not context.get("execution_result"):
                # Run persistence specifically if not already run during Phase 9
                plan = context["load_plan"]
                strategy = SequentialExecutionStrategy()
                exec_context = ExecutionContext(
                    plan=plan,
                    shared_state={"institution_id": tenant_id, "tenant_id": tenant_id, "is_dry_run": is_dry_run},
                )
                exec_result = strategy.execute_plan(exec_context, executor=self.step_executor)
                context["execution_result"] = exec_result
                if getattr(exec_result, "failed_steps", 0) > 0:
                    raise MacError(f"Persistence failed on {exec_result.failed_steps} steps")

            tracker.end_phase("Persistence Adapter", start_p, True, input_cnt, input_cnt)
            tracker.transition_to(SessionState.COMPLETED)
        except Exception as exc:
            tracker.end_phase("Persistence Adapter", start_p, False, input_cnt, input_cnt, [str(exc)])
            tracker.abort_session(f"Persistence phase failed: {exc}", SessionState.FAILED)
            return tracker.build_report(context)

        return tracker.build_report(context)


def _to_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        return [str(v) for v in val]
    return []


def _get_record_count(context: Dict[str, Any]) -> int:
    payload = context.get("payload", {})
    if isinstance(payload, dict):
        for key in ("staged_records", "mapped_records", "parsed_records", "raw_data", "records"):
            val = payload.get(key)
            if isinstance(val, (list, tuple, dict)):
                return len(val)
    elif isinstance(payload, (list, tuple)):
        return len(payload)
    return 0
