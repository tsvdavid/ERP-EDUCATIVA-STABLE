# apps/data_engine/quality/engine.py
"""Central Quality Engine implementation and integration adapters."""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from apps.data_engine.components.base import BaseComponent, MacContext
from apps.data_engine.events.dispatcher import EventEnvelope
from apps.data_engine.events.models import EventCategory
from apps.data_engine.events.registry import EventBusRegistry
from apps.data_engine.progress.registry import ProgressRegistry
from apps.data_engine.transformations.base import BaseTransformation
from apps.data_engine.transformations.contracts import TransformationContext
from apps.data_engine.transformations.models import TransformationError

from apps.data_engine.quality.base import BaseQualityEngine, BaseQualityRule
from apps.data_engine.quality.exceptions import RuleException
from apps.data_engine.quality.models import (
    QualityReport,
    QualityRuleResult,
    QualityStatistics,
    QualityViolation,
)
from apps.data_engine.quality.scorer import QualityScorer


class QualityEngine(BaseQualityEngine):
    """Executes rules, collects violations, scores quality, emits events, and updates progress."""

    def __init__(self, scorer: Optional[QualityScorer] = None) -> None:
        self.scorer = scorer or QualityScorer()

    def execute(
        self,
        records: List[Dict[str, Any]],
        session_id: str,
        template_code: str,
        rules: Optional[List[BaseQualityRule]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> QualityReport:
        """Run all validators across records. Computes stats and scores, triggers progress & events."""
        start_time = time.perf_counter()
        rules_to_run = rules if rules is not None else []
        ctx = context if context is not None else {}

        violations_by_record: Dict[int, List[QualityViolation]] = {}
        
        info_count = 0
        warning_count = 0
        error_count = 0
        critical_count = 0
        total_violations = 0
        passed_records = 0
        failed_records = 0

        for idx, record in enumerate(records):
            rec_violations: List[QualityViolation] = []
            for rule in rules_to_run:
                try:
                    res = rule.validate(record, ctx)
                    if res:
                        rec_violations.extend(res)
                except Exception as exc:
                    raise RuleException(f"Rule evaluation failed for '{rule.code}': {exc}") from exc
            
            if rec_violations:
                violations_by_record[idx] = rec_violations
                total_violations += len(rec_violations)
                
                # Severity counters
                has_failures = False
                for v in rec_violations:
                    sev = v.severity.upper()
                    if sev == "INFO":
                        info_count += 1
                    elif sev == "WARNING":
                        warning_count += 1
                    elif sev == "ERROR":
                        error_count += 1
                        has_failures = True
                    elif sev == "CRITICAL":
                        critical_count += 1
                        has_failures = True
                
                if has_failures:
                    failed_records += 1
                else:
                    passed_records += 1
            else:
                passed_records += 1

        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000.0

        # Build stats
        stats = QualityStatistics(
            total_records=len(records),
            passed_records=passed_records,
            failed_records=failed_records,
            total_violations=total_violations,
            info_count=info_count,
            warning_count=warning_count,
            error_count=error_count,
            critical_count=critical_count,
            execution_time_ms=execution_time_ms,
            rules_executed=len(rules_to_run),
        )

        # Compute Score
        score = self.scorer.score_run(violations_by_record, len(records))

        report = QualityReport(
            session_id=session_id,
            template_code=template_code,
            statistics=stats,
            score=score,
            violations_by_record=violations_by_record,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Notify ProgressTracker
        try:
            tracker = ProgressRegistry.global_registry().get(session_id)
            if tracker:
                tracker.record_phase_progress(
                    phase_name="QUALITY_CHECK",
                    processed=len(records),
                    accepted=passed_records,
                    rejected=failed_records,
                    skipped=0,
                    message="Data quality rule validation completed.",
                )
        except Exception:
            pass

        # Publish Event Envelope
        try:
            dispatcher = EventBusRegistry.global_registry().get_dispatcher()
            seq = dispatcher.next_sequence(session_id)
            envelope = EventEnvelope.create(
                category=EventCategory.EXECUTION,
                event_type="DATA_QUALITY_REPORT",
                session_id=session_id,
                payload=report.to_dict(),
                source="quality",
                sequence_number=seq,
            )
            dispatcher.publish(envelope)
        except Exception:
            pass

        return report


class QualityRuleTransformationAdapter(BaseTransformation):
    """Adapts a BaseQualityRule so it can run as a step in a TransformationPipeline."""

    component_type = "transformation"

    def __init__(self, rule: BaseQualityRule, context: Optional[TransformationContext] = None) -> None:
        super().__init__(context=context)
        self._rule = rule

    @property
    def name(self) -> str:
        return f"quality_{self._rule.code}"

    @property
    def description(self) -> str:
        return f"Data Quality Rule Adapter for {self._rule.code}"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return True

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        # Quality rules do not mutate data, simply pass-through
        return record

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        # Safely obtain a rule context dict from self.context
        if self.context and hasattr(self.context, "variables") and isinstance(self.context.variables, dict):
            rule_context = self.context.variables.setdefault("rule_context", {})
        else:
            rule_context = {}

        violations = self._rule.validate(record, rule_context)
        
        errors = []
        for v in violations:
            # Map ERROR and CRITICAL violations to pipeline execution blocks
            if v.severity.upper() in ("ERROR", "CRITICAL"):
                errors.append(
                    TransformationError(
                        error_code=v.rule_code,
                        error_message=v.message,
                        transformation_name=self.name,
                        field_name=self._rule.field,
                        original_value=v.value,
                    )
                )
        return errors


class QualityWorkflowComponent(BaseComponent):
    """Wraps the QualityEngine as a pipeline step inside ImportWorkflowOrchestrator."""

    component_type = "quality_verifier"

    def __init__(
        self,
        engine: BaseQualityEngine,
        rules: List[BaseQualityRule],
        template_code: str = "workflow_template",
        name: str = "quality_verifier",
    ) -> None:
        super().__init__()
        self._engine = engine
        self._rules = rules
        self._template_code = template_code
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def execute(self, context: MacContext) -> Dict[str, Any]:
        payload = context.get("payload", {})
        records = payload.get("records") or []
        session_id = context.get("run_id") or "workflow_session"

        # Execute quality rules check
        report = self._engine.execute(
            records=records,
            session_id=session_id,
            template_code=self._template_code,
            rules=self._rules,
            context=context,
        )

        # Split records into accepted and rejected lists
        accepted_records = []
        rejected_records = []
        for idx, rec in enumerate(records):
            rec_violations = report.violations_by_record.get(idx, [])
            if any(v.severity.upper() in ("ERROR", "CRITICAL") for v in rec_violations):
                rejected_records.append(rec)
            else:
                accepted_records.append(rec)

        out_payload = dict(payload)
        out_payload["records"] = accepted_records
        out_payload["rejected_records"] = rejected_records
        out_payload["quality_report"] = report.to_dict()

        return {"payload": out_payload}
