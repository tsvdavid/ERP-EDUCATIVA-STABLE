# apps/data_engine/pipeline/executor.py
"""PipelineExecutor coordinating sequential pipeline execution, event publication, and progress tracking updates."""

import datetime
import time
import uuid
from typing import Any, Dict, List, Optional

from apps.data_engine.events.dispatcher import EventEnvelope
from apps.data_engine.events.subscribers import CallbackEventSubscriber
from apps.data_engine.events.models import EventCategory
from apps.data_engine.events.registry import EventBusRegistry
from apps.data_engine.progress.registry import ProgressRegistry
from apps.data_engine.progress.tracker import ProgressTracker

from apps.data_engine.pipeline.exceptions import PipelineExecutionError
from apps.data_engine.pipeline.models import PipelineExecutionReport
from apps.data_engine.pipeline.runtime import PipelineRuntime
from apps.data_engine.pipeline.adapters import (
    PipelineQualityAdapter,
    PipelineBusinessAdapter,
    PipelineWorkflowAdapter,
)


class PipelineExecutor:
    """Coordinates and executes a PipelineRuntime sequentially, emitting progress and events."""

    def execute(
        self,
        runtime: PipelineRuntime,
        tenant_id: str,
        user_id: str,
        run_id: Optional[str] = None,
        is_dry_run: bool = False,
        step_executor: Optional[Any] = None,
    ) -> PipelineExecutionReport:
        """Execute the pipeline steps in sequential order.

        Flow:
        Connector -> Template -> Transformation Pipeline -> Quality Engine -> Business Rules Engine -> Workflow -> Report
        """
        if not isinstance(runtime, PipelineRuntime):
            raise TypeError("runtime must be an instance of PipelineRuntime.")
        if not tenant_id:
            raise ValueError("tenant_id is required.")
        if not user_id:
            raise ValueError("user_id is required.")

        session_id = run_id or str(uuid.uuid4())
        start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        start_t = time.perf_counter()

        # Initialize event subscriber to capture all execution events
        dispatcher = EventBusRegistry.global_registry().get_dispatcher()
        collected_events = []

        def event_callback(envelope: EventEnvelope) -> None:
            if envelope.session_id == session_id:
                collected_events.append(envelope.to_dict())

        subscriber = CallbackEventSubscriber(event_callback)
        dispatcher.subscribe(subscriber)

        # Initialize ProgressTracker
        tracker = ProgressRegistry.global_registry().get(session_id)
        if not tracker:
            tracker = ProgressTracker(session_id=session_id, run_id=session_id)
            ProgressRegistry.global_registry().register(session_id, tracker)

        def publish_pipeline_event(event_type: str, payload: Dict[str, Any]) -> None:
            try:
                seq = dispatcher.next_sequence(session_id)
                env = EventEnvelope.create(
                    category=EventCategory.EXECUTION,
                    event_type=event_type,
                    session_id=session_id,
                    payload=payload,
                    source="pipeline",
                    sequence_number=seq,
                )
                dispatcher.publish(env)
            except Exception:
                pass

        try:
            # Emit PIPELINE_STARTED
            publish_pipeline_event(
                "PIPELINE_STARTED",
                {
                    "pipeline_id": getattr(runtime.template, "code", "declarative_pipeline") if runtime.template else "declarative_pipeline",
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                },
            )

            # 1. CONNECTOR PHASE
            tracker.record_phase_progress(
                phase_name="CONNECTOR",
                processed=0,
                accepted=0,
                rejected=0,
                message="Fetching records from connector...",
            )
            try:
                raw_records = runtime.connector.fetch()
                if not isinstance(raw_records, list):
                    raw_records = list(raw_records)
            except Exception as exc:
                raise PipelineExecutionError(f"Connector fetch phase failed: {exc}") from exc

            total_records = len(raw_records)
            tracker.record_phase_progress(
                phase_name="CONNECTOR",
                processed=total_records,
                accepted=total_records,
                rejected=0,
                message=f"Fetched {total_records} raw records from connector.",
            )

            # 2 & 3. TEMPLATE & TRANSFORMATION PIPELINE PHASE
            tracker.record_phase_progress(
                phase_name="TRANSFORMATION",
                processed=total_records,
                accepted=0,
                rejected=0,
                message="Running transformation pipeline...",
            )
            try:
                tx_report = runtime.transformations.execute(raw_records)
            except Exception as exc:
                raise PipelineExecutionError(f"Transformation phase failed: {exc}") from exc

            accepted_records = [
                res.transformed_record for res in tx_report.results if res.status != "REJECTED"
            ]
            rejected_records_count = total_records - len(accepted_records)

            tracker.record_phase_progress(
                phase_name="TRANSFORMATION",
                processed=total_records,
                accepted=len(accepted_records),
                rejected=rejected_records_count,
                message=f"Transformation complete. Accepted: {len(accepted_records)}, Rejected: {rejected_records_count}",
            )

            # 4. QUALITY ENGINE PHASE
            quality_score = 100.0
            if runtime.quality_engine and runtime.configuration.get("quality_rules"):
                tracker.record_phase_progress(
                    phase_name="QUALITY_CHECK",
                    processed=len(accepted_records),
                    accepted=0,
                    rejected=0,
                    message="Running data quality checks...",
                )
                quality_rules = runtime.configuration["quality_rules"]
                template_code = runtime.template.code if runtime.template else "pipeline_template"
                quality_adapter = PipelineQualityAdapter(runtime.quality_engine, quality_rules, template_code)
                try:
                    q_report = quality_adapter.execute(accepted_records, session_id)
                    quality_score = q_report.score
                except Exception as exc:
                    raise PipelineExecutionError(f"Quality check phase failed: {exc}") from exc

                accepted_after_q = []
                rejected_after_q = []
                for idx, rec in enumerate(accepted_records):
                    rec_violations = q_report.violations_by_record.get(idx, [])
                    if any(v.severity.upper() in ("ERROR", "CRITICAL") for v in rec_violations):
                        rejected_after_q.append(rec)
                    else:
                        accepted_after_q.append(rec)

                q_rejected_cnt = len(rejected_after_q)
                accepted_records = accepted_after_q
                rejected_records_count += q_rejected_cnt

                tracker.record_phase_progress(
                    phase_name="QUALITY_CHECK",
                    processed=len(accepted_records) + q_rejected_cnt,
                    accepted=len(accepted_records),
                    rejected=q_rejected_cnt,
                    message=f"Quality check complete. Accepted: {len(accepted_records)}, Rejected: {q_rejected_cnt}",
                )

            # 5. BUSINESS RULES ENGINE PHASE
            business_violations = []
            if runtime.business_engine and runtime.configuration.get("business_rules"):
                tracker.record_phase_progress(
                    phase_name="BUSINESS_RULES",
                    processed=len(accepted_records),
                    accepted=0,
                    rejected=0,
                    message="Running business rules checks...",
                )
                business_rules = runtime.configuration["business_rules"]
                business_adapter = PipelineBusinessAdapter(runtime.business_engine, business_rules)
                try:
                    b_report = business_adapter.execute(accepted_records, session_id)
                except Exception as exc:
                    raise PipelineExecutionError(f"Business rules check phase failed: {exc}") from exc

                accepted_after_b = []
                rejected_after_b = []
                for idx, rec in enumerate(accepted_records):
                    rec_result = b_report.results_by_record.get(idx, [])
                    violations = [res.violation for res in rec_result if not res.passed and res.violation]
                    if violations:
                        rejected_after_b.append(rec)
                        for v in violations:
                            business_violations.append(v.to_dict())
                    else:
                        accepted_after_b.append(rec)

                b_rejected_cnt = len(rejected_after_b)
                accepted_records = accepted_after_b
                rejected_records_count += b_rejected_cnt

                tracker.record_phase_progress(
                    phase_name="BUSINESS_RULES",
                    processed=len(accepted_records) + b_rejected_cnt,
                    accepted=len(accepted_records),
                    rejected=b_rejected_cnt,
                    message=f"Business rules check complete. Accepted: {len(accepted_records)}, Rejected: {b_rejected_cnt}",
                )

            # 6. WORKFLOW PHASE
            workflow_summary = {}
            if runtime.workflow:
                tracker.record_phase_progress(
                    phase_name="WORKFLOW",
                    processed=len(accepted_records),
                    accepted=0,
                    rejected=0,
                    message="Orchestrating load planning and persistence...",
                )
                workflow_adapter = PipelineWorkflowAdapter(runtime.workflow)
                target_entity = runtime.template.get_template_definition().target_entity if runtime.template else "UnknownEntity"
                try:
                    wf_report = workflow_adapter.execute(
                        records=accepted_records,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        run_id=session_id,
                        is_dry_run=is_dry_run,
                        step_executor=step_executor,
                        loader_type=runtime.configuration.get("loader_type", "default"),
                        target_entity=target_entity,
                    )
                    workflow_summary = wf_report.to_dict() if hasattr(wf_report, "to_dict") else {}
                except Exception as exc:
                    raise PipelineExecutionError(f"Workflow execution phase failed: {exc}") from exc

                tracker.record_phase_progress(
                    phase_name="WORKFLOW",
                    processed=len(accepted_records),
                    accepted=len(accepted_records),
                    rejected=0,
                    message="Workflow orchestration complete.",
                )

            # Finish timing
            finish_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
            duration = time.perf_counter() - start_t

            summary = {
                "is_dry_run": is_dry_run,
                "workflow_summary": workflow_summary,
            }

            # Emit PIPELINE_COMPLETED
            publish_pipeline_event(
                "PIPELINE_COMPLETED",
                {
                    "pipeline_id": getattr(runtime.template, "code", "declarative_pipeline") if runtime.template else "declarative_pipeline",
                    "processed": total_records,
                    "accepted": len(accepted_records),
                    "rejected": rejected_records_count,
                    "duration_seconds": duration,
                },
            )

            # Build report
            report = PipelineExecutionReport(
                pipeline_id=getattr(runtime.template, "code", "declarative_pipeline") if runtime.template else "declarative_pipeline",
                run_id=session_id,
                start_time=start_time,
                finish_time=finish_time,
                duration=duration,
                processed=total_records,
                accepted=len(accepted_records),
                rejected=rejected_records_count,
                quality_score=quality_score,
                business_violations=business_violations,
                events=list(collected_events),
                summary=summary,
            )

            return report

        except Exception as exc:
            # Emit PIPELINE_FAILED
            publish_pipeline_event(
                "PIPELINE_FAILED",
                {
                    "pipeline_id": getattr(runtime.template, "code", "declarative_pipeline") if runtime.template else "declarative_pipeline",
                    "error": str(exc),
                },
            )
            raise PipelineExecutionError(f"Pipeline execution aborted: {exc}") from exc

        finally:
            # Unsubscribe event listener to avoid memory leaks
            dispatcher.unsubscribe(subscriber)
