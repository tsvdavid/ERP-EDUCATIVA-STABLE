# apps/data_engine/integration/services.py
"""Integration service coordinating mapping, persistence, transaction, and event flows."""

import time
from typing import Any, Dict, List, Optional

from apps.data_engine.events.models import EventEnvelope, EventCategory
from apps.data_engine.events.registry import EventBusRegistry
from apps.data_engine.progress.registry import ProgressRegistry

from .contracts import BaseIntegrationService, BaseTransactionManager
from .dto import BatchPersistenceResult
from .exceptions import PersistenceError
from .registry import IntegrationRegistry
from .transaction import InMemoryTransactionManager


class MacIntegrationService(BaseIntegrationService):
    """High-level service coordinating transactions, mappings, persistence, progress, and events."""

    def __init__(
        self,
        registry: Optional[IntegrationRegistry] = None,
        transaction_manager: Optional[BaseTransactionManager] = None,
    ) -> None:
        self.registry = registry or IntegrationRegistry.global_registry()
        self.transaction_manager = transaction_manager or InMemoryTransactionManager()

    def integrate(
        self,
        entity_name: str,
        records: List[Dict[str, Any]],
        tenant_id: str,
        user_id: str,
        run_id: str,
        is_dry_run: bool = False,
    ) -> BatchPersistenceResult:
        start_time = time.monotonic()
        dispatcher = EventBusRegistry.global_registry().get_dispatcher()
        tracker = ProgressRegistry.global_registry().get(run_id)

        # 1. Notify Progress Tracker (Phase Start)
        if tracker is not None:
            tracker.record_phase_start("Persistence Adapter", total_records=len(records))

        # 2. Publish Event PERSISTENCE_STARTED
        if dispatcher is not None:
            seq = dispatcher.next_sequence(run_id)
            envelope = EventEnvelope.create(
                category=EventCategory.EXECUTION,
                event_type="PERSISTENCE_STARTED",
                session_id=run_id,
                payload={
                    "entity_name": entity_name,
                    "records_count": len(records),
                    "is_dry_run": is_dry_run,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                },
                source="integration",
                sequence_number=seq,
                tenant_id=tenant_id,
                institution_id=tenant_id,
            )
            dispatcher.publish(envelope)

        # Retrieve adapter for target entity
        adapter = self.registry.get(entity_name)

        try:
            # 3. Transaction manager boundary
            with self.transaction_manager as tx:
                context = {
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "is_dry_run": is_dry_run,
                }
                result = adapter.persist_batch(records, context=context)

                if result.failed_count > 0:
                    tx.rollback()

            duration_ms = (time.monotonic() - start_time) * 1000.0

            # 4. Notify Progress Tracker (Phase Progress and End)
            if tracker is not None:
                tracker.record_phase_progress(
                    phase_name="Persistence Adapter",
                    processed=result.processed_count,
                    accepted=result.success_count,
                    rejected=result.failed_count,
                    message=f"Persistence batch finished: {result.success_count} success, {result.failed_count} failures.",
                )
                tracker.record_phase_end(
                    phase_name="Persistence Adapter",
                    success=(result.failed_count == 0),
                    output_records=result.success_count,
                )

            # 5. Publish Event PERSISTENCE_COMPLETED / PERSISTENCE_FAILED
            if dispatcher is not None:
                event_type = "PERSISTENCE_COMPLETED" if result.failed_count == 0 else "PERSISTENCE_FAILED"
                seq = dispatcher.next_sequence(run_id)
                envelope = EventEnvelope.create(
                    category=EventCategory.EXECUTION,
                    event_type=event_type,
                    session_id=run_id,
                    payload={
                        "entity_name": entity_name,
                        "processed_count": result.processed_count,
                        "success_count": result.success_count,
                        "failed_count": result.failed_count,
                        "duration_ms": duration_ms,
                    },
                    source="integration",
                    sequence_number=seq,
                    tenant_id=tenant_id,
                    institution_id=tenant_id,
                )
                dispatcher.publish(envelope)

            return result

        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000.0
            try:
                self.transaction_manager.rollback()
            except Exception:
                pass

            if tracker is not None:
                tracker.record_phase_progress(
                    phase_name="Persistence Adapter",
                    processed=len(records),
                    accepted=0,
                    rejected=len(records),
                    message=f"Persistence failed: {e}",
                )
                tracker.record_phase_end(
                    phase_name="Persistence Adapter",
                    success=False,
                    output_records=0,
                    errors=[str(e)],
                )

            if dispatcher is not None:
                seq = dispatcher.next_sequence(run_id)
                envelope = EventEnvelope.create(
                    category=EventCategory.EXECUTION,
                    event_type="PERSISTENCE_FAILED",
                    session_id=run_id,
                    payload={
                        "entity_name": entity_name,
                        "error": str(e),
                        "duration_ms": duration_ms,
                    },
                    source="integration",
                    sequence_number=seq,
                    tenant_id=tenant_id,
                    institution_id=tenant_id,
                )
                dispatcher.publish(envelope)

            raise PersistenceError(f"Integration service failed: {e}") from e
