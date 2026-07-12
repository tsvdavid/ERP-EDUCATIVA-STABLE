# apps/data_engine/events/tests/test_tarea21.py
"""Comprehensive test suite for the MAC Real-Time Event Bus & Notification Framework (TAREA 21).

Validates:
1. Domain models and abstract contracts (``TestEventModelsAndContracts``).
2. Core dispatcher pub/sub, category filtering, and exception safety (``TestEventDispatcherCore``).
3. Per-session replay buffer with sequence ordering and cap enforcement (``TestEventReplayBuffer``).
4. Standard subscriber implementations (``TestSubscriberImplementations``).
5. Thread-safe concurrent publishing (``TestEventBusThreadSafety``).
6. Bridge Observer integration with ProgressTracker (``TestBridgeObserverIntegration``).
7. End-to-end workflow: Orchestrator → ProgressTracker → Bridge → EventBus (``TestEventBusOrchestratorE2E``).
8. JSON serialization round-trip (``TestEventSerializer``).
9. Zero-ORM enforcement across the entire ``events/`` package (``TestZeroOrmIsolation``).
"""

import json
import logging
import os
import sys
import threading

import pytest

workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
backend_dir = os.path.join(workspace_root, "backend")
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.data_engine.components.base import BaseComponent, MacContext
from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.events.base import BaseEventDispatcher, BaseEventSubscriber
from apps.data_engine.events.dispatcher import EventBusBridgeObserver, EventDispatcher
from apps.data_engine.events.models import EventCategory, EventEnvelope
from apps.data_engine.events.registry import EventBusRegistry
from apps.data_engine.events.serializers import EventSerializer
from apps.data_engine.events.subscribers import (
    CallbackEventSubscriber,
    FilteredEventSubscriber,
    InMemoryEventSubscriber,
    LoggingEventSubscriber,
)
from apps.data_engine.progress.models import ProgressEventType
from apps.data_engine.progress.observers import InMemoryProgressObserver
from apps.data_engine.progress.registry import ProgressRegistry
from apps.data_engine.progress.tracker import ProgressTracker
from apps.data_engine.sessions.orchestrator import ImportWorkflowOrchestrator


@pytest.fixture(autouse=True)
def clean_registries():
    """Ensure clean MAC, Progress, and EventBus registries before each test."""
    MacRegistry.global_registry()._components.clear()
    ProgressRegistry.global_registry().clear()
    EventBusRegistry.global_registry().reset()
    yield
    MacRegistry.global_registry()._components.clear()
    ProgressRegistry.global_registry().clear()
    EventBusRegistry.global_registry().reset()


# ===========================================================================
# 1. Domain Models and Abstract Contracts
# ===========================================================================
class TestEventModelsAndContracts:
    def test_abstract_contracts_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            BaseEventSubscriber()  # type: ignore[abstract]
        with pytest.raises(TypeError):
            BaseEventDispatcher()  # type: ignore[abstract]

    def test_event_category_enum_values(self):
        assert EventCategory.PROGRESS == "PROGRESS"
        assert EventCategory.SESSION == "SESSION"
        assert EventCategory.EXECUTION == "EXECUTION"
        assert EventCategory.SYSTEM == "SYSTEM"
        assert len(EventCategory) == 4

    def test_event_envelope_immutability_and_serialization(self):
        envelope = EventEnvelope.create(
            category=EventCategory.PROGRESS,
            event_type="PHASE_PROGRESS",
            session_id="s1",
            payload={"records_processed": 42},
            source="progress",
            sequence_number=7,
            tenant_id="tenant_123",
            institution_id="inst_456",
            metadata={"tenant": "t1"},
        )
        assert envelope.envelope_id is not None
        assert envelope.category == EventCategory.PROGRESS
        assert envelope.sequence_number == 7
        assert envelope.tenant_id == "tenant_123"
        assert envelope.institution_id == "inst_456"

        # Immutability
        with pytest.raises(Exception):
            envelope.session_id = "s2"  # type: ignore[misc]

        # Serialization
        d = envelope.to_dict()
        assert d["category"] == "PROGRESS"
        assert d["event_type"] == "PHASE_PROGRESS"
        assert d["payload"]["records_processed"] == 42
        assert d["metadata"]["tenant"] == "t1"
        assert d["sequence_number"] == 7
        assert d["tenant_id"] == "tenant_123"
        assert d["institution_id"] == "inst_456"


# ===========================================================================
# 2. Core Dispatcher Pub/Sub
# ===========================================================================
class TestEventDispatcherCore:
    def test_publish_delivers_to_all_subscribers(self):
        dispatcher = EventDispatcher()
        sub1 = InMemoryEventSubscriber()
        sub2 = InMemoryEventSubscriber()
        dispatcher.subscribe(sub1)
        dispatcher.subscribe(sub2)

        envelope = EventEnvelope.create(
            category=EventCategory.PROGRESS,
            event_type="TEST_EVENT",
            session_id="s1",
            payload={},
            source="test",
            sequence_number=0,
        )
        dispatcher.publish(envelope)

        assert len(sub1.get_events()) == 1
        assert len(sub2.get_events()) == 1
        assert sub1.get_events()[0].envelope_id == envelope.envelope_id

    def test_category_filtering_at_subscribe_level(self):
        dispatcher = EventDispatcher()
        progress_only = InMemoryEventSubscriber()
        session_only = InMemoryEventSubscriber()
        all_events = InMemoryEventSubscriber()

        dispatcher.subscribe(progress_only, categories={EventCategory.PROGRESS})
        dispatcher.subscribe(session_only, categories={EventCategory.SESSION})
        dispatcher.subscribe(all_events)

        progress_env = EventEnvelope.create(
            category=EventCategory.PROGRESS, event_type="P", session_id="s1",
            payload={}, source="progress", sequence_number=0,
        )
        session_env = EventEnvelope.create(
            category=EventCategory.SESSION, event_type="S", session_id="s1",
            payload={}, source="session", sequence_number=1,
        )
        dispatcher.publish(progress_env)
        dispatcher.publish(session_env)

        assert len(progress_only.get_events()) == 1
        assert progress_only.get_events()[0].event_type == "P"
        assert len(session_only.get_events()) == 1
        assert session_only.get_events()[0].event_type == "S"
        assert len(all_events.get_events()) == 2

    def test_unsubscribe_stops_delivery(self):
        dispatcher = EventDispatcher()
        sub = InMemoryEventSubscriber()
        dispatcher.subscribe(sub)

        env1 = EventEnvelope.create(
            category=EventCategory.SYSTEM, event_type="E1", session_id="s1",
            payload={}, source="test", sequence_number=0,
        )
        dispatcher.publish(env1)
        assert len(sub.get_events()) == 1

        dispatcher.unsubscribe(sub)
        env2 = EventEnvelope.create(
            category=EventCategory.SYSTEM, event_type="E2", session_id="s1",
            payload={}, source="test", sequence_number=1,
        )
        dispatcher.publish(env2)
        assert len(sub.get_events()) == 1  # no new events

    def test_subscriber_exception_does_not_crash_bus(self):
        dispatcher = EventDispatcher()

        class CrashingSubscriber(BaseEventSubscriber):
            def on_event(self, envelope):
                raise RuntimeError("Boom!")

        good_sub = InMemoryEventSubscriber()
        dispatcher.subscribe(CrashingSubscriber())
        dispatcher.subscribe(good_sub)

        env = EventEnvelope.create(
            category=EventCategory.SYSTEM, event_type="E", session_id="s1",
            payload={}, source="test", sequence_number=0,
        )
        dispatcher.publish(env)  # Should not raise
        assert len(good_sub.get_events()) == 1

    def test_invalid_subscriber_type_raises(self):
        dispatcher = EventDispatcher()
        with pytest.raises(TypeError, match="BaseEventSubscriber"):
            dispatcher.subscribe("not a subscriber")  # type: ignore[arg-type]


# ===========================================================================
# 3. Replay Buffer
# ===========================================================================
class TestEventReplayBuffer:
    def test_replay_returns_buffered_events_in_order(self):
        dispatcher = EventDispatcher()
        for i in range(5):
            env = EventEnvelope.create(
                category=EventCategory.PROGRESS, event_type="P",
                session_id="replay_session", payload={"i": i},
                source="test", sequence_number=i,
            )
            dispatcher.publish(env)

        replayed = dispatcher.replay("replay_session")
        assert len(replayed) == 5
        assert [e.sequence_number for e in replayed] == [0, 1, 2, 3, 4]

    def test_replay_since_sequence_filters_old_events(self):
        dispatcher = EventDispatcher()
        for i in range(5):
            env = EventEnvelope.create(
                category=EventCategory.PROGRESS, event_type="P",
                session_id="s_replay", payload={},
                source="test", sequence_number=i,
            )
            dispatcher.publish(env)

        replayed = dispatcher.replay("s_replay", since_sequence=3)
        assert len(replayed) == 2
        assert [e.sequence_number for e in replayed] == [3, 4]

    def test_replay_buffer_respects_max_size(self):
        dispatcher = EventDispatcher(max_replay_buffer_size=3)
        for i in range(10):
            env = EventEnvelope.create(
                category=EventCategory.PROGRESS, event_type="P",
                session_id="capped", payload={},
                source="test", sequence_number=i,
            )
            dispatcher.publish(env)

        replayed = dispatcher.replay("capped")
        assert len(replayed) == 3
        # Should retain the last 3 events (seq 7, 8, 9)
        assert [e.sequence_number for e in replayed] == [7, 8, 9]

    def test_clear_session_removes_buffer(self):
        dispatcher = EventDispatcher()
        env = EventEnvelope.create(
            category=EventCategory.SESSION, event_type="S", session_id="to_clear",
            payload={}, source="test", sequence_number=0,
        )
        dispatcher.publish(env)
        assert len(dispatcher.replay("to_clear")) == 1

        dispatcher.clear_session("to_clear")
        assert len(dispatcher.replay("to_clear")) == 0


# ===========================================================================
# 4. Subscriber Implementations
# ===========================================================================
class TestSubscriberImplementations:
    def test_in_memory_subscriber_query_methods(self):
        sub = InMemoryEventSubscriber()
        e1 = EventEnvelope.create(
            category=EventCategory.PROGRESS, event_type="P", session_id="s1",
            payload={}, source="test", sequence_number=0,
        )
        e2 = EventEnvelope.create(
            category=EventCategory.SESSION, event_type="S", session_id="s2",
            payload={}, source="test", sequence_number=1,
        )
        sub.on_event(e1)
        sub.on_event(e2)

        assert len(sub.get_events()) == 2
        assert len(sub.get_events_by_category(EventCategory.PROGRESS)) == 1
        assert len(sub.get_events_by_session("s2")) == 1

        sub.clear()
        assert len(sub.get_events()) == 0

    def test_callback_subscriber_invokes_function(self):
        received = []
        sub = CallbackEventSubscriber(lambda e: received.append(e))
        env = EventEnvelope.create(
            category=EventCategory.SYSTEM, event_type="T", session_id="s1",
            payload={}, source="test", sequence_number=0,
        )
        sub.on_event(env)
        assert len(received) == 1
        assert received[0].envelope_id == env.envelope_id

    def test_callback_subscriber_rejects_non_callable(self):
        with pytest.raises(TypeError, match="callable"):
            CallbackEventSubscriber("not callable")  # type: ignore[arg-type]

    def test_logging_subscriber_writes_log(self, caplog):
        caplog.set_level(logging.INFO)
        sub = LoggingEventSubscriber()
        env = EventEnvelope.create(
            category=EventCategory.EXECUTION, event_type="STEP_START",
            session_id="log_session", payload={}, source="execution", sequence_number=5,
        )
        sub.on_event(env)
        assert "EventBus" in caplog.text
        assert "EXECUTION" in caplog.text
        assert "STEP_START" in caplog.text

    def test_filtered_subscriber_filters_by_criteria(self):
        inner = InMemoryEventSubscriber()
        filtered = FilteredEventSubscriber(
            inner,
            categories={EventCategory.PROGRESS},
            event_types={"PHASE_PROGRESS"},
            session_ids={"target_session"},
        )

        # Should pass all filters
        good = EventEnvelope.create(
            category=EventCategory.PROGRESS, event_type="PHASE_PROGRESS",
            session_id="target_session", payload={}, source="test", sequence_number=0,
        )
        # Wrong category
        bad_cat = EventEnvelope.create(
            category=EventCategory.SESSION, event_type="PHASE_PROGRESS",
            session_id="target_session", payload={}, source="test", sequence_number=1,
        )
        # Wrong event_type
        bad_type = EventEnvelope.create(
            category=EventCategory.PROGRESS, event_type="SESSION_START",
            session_id="target_session", payload={}, source="test", sequence_number=2,
        )
        # Wrong session_id
        bad_sid = EventEnvelope.create(
            category=EventCategory.PROGRESS, event_type="PHASE_PROGRESS",
            session_id="other_session", payload={}, source="test", sequence_number=3,
        )

        for env in (good, bad_cat, bad_type, bad_sid):
            filtered.on_event(env)

        assert len(inner.get_events()) == 1
        assert inner.get_events()[0].envelope_id == good.envelope_id


# ===========================================================================
# 5. Thread Safety
# ===========================================================================
class TestEventBusThreadSafety:
    def test_concurrent_publish_from_multiple_threads(self):
        dispatcher = EventDispatcher()
        sub = InMemoryEventSubscriber()
        dispatcher.subscribe(sub)

        def worker(thread_id):
            for i in range(20):
                seq = dispatcher.next_sequence("thread_test")
                env = EventEnvelope.create(
                    category=EventCategory.PROGRESS, event_type="THREAD_EVENT",
                    session_id="thread_test", payload={"thread": thread_id, "i": i},
                    source="test", sequence_number=seq,
                )
                dispatcher.publish(env)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        events = sub.get_events()
        assert len(events) == 200  # 10 threads × 20 events
        # Verify all sequence numbers are unique
        sequences = [e.sequence_number for e in events]
        assert len(set(sequences)) == 200


# ===========================================================================
# 6. Bridge Observer Integration with ProgressTracker
# ===========================================================================
class TestBridgeObserverIntegration:
    def test_bridge_converts_progress_events_to_envelopes(self):
        dispatcher = EventDispatcher()
        sub = InMemoryEventSubscriber()
        dispatcher.subscribe(sub)

        bridge = EventBusBridgeObserver(dispatcher)

        tracker = ProgressTracker("bridge_session", total_expected_records=10)
        tracker.subscribe(bridge)

        tracker.record_session_start()
        tracker.record_phase_start("Reader")
        tracker.record_phase_progress("Reader", processed=5, accepted=5)
        tracker.record_session_end()

        events = sub.get_events()
        assert len(events) == 4
        assert all(e.category == EventCategory.PROGRESS for e in events)
        assert all(e.source == "progress" for e in events)
        assert all(e.session_id == "bridge_session" for e in events)

        # Verify sequence ordering
        seqs = [e.sequence_number for e in events]
        assert seqs == sorted(seqs)
        assert len(set(seqs)) == 4  # all unique

        # Verify event types preserved
        types = [e.event_type for e in events]
        assert types[0] == "SESSION_START"
        assert types[1] == "PHASE_START"
        assert types[2] == "PHASE_PROGRESS"
        assert types[3] == "SESSION_END"

        # Verify payload contains full snapshot
        assert "snapshot" in events[2].payload
        assert events[2].payload["snapshot"]["records_processed"] == 5

    def test_bridge_rejects_invalid_dispatcher(self):
        with pytest.raises(TypeError, match="BaseEventDispatcher"):
            EventBusBridgeObserver("not a dispatcher")  # type: ignore[arg-type]


# ===========================================================================
# 7. End-to-End: Orchestrator → ProgressTracker → Bridge → EventBus
# ===========================================================================
class DummyReaderComponent(BaseComponent):
    component_type = "reader"

    def execute(self, context: MacContext):  # type: ignore[override]
        return {"payload": {"records": [{"id": 1}, {"id": 2}]}}


class DummyParserComponent(BaseComponent):
    component_type = "parser"

    def execute(self, context: MacContext):  # type: ignore[override]
        records = context.get("payload", {}).get("records", [])
        return {"payload": {"parsed_records": records}}


class DummyMapperComponent(BaseComponent):
    component_type = "mapper"

    def execute(self, context: MacContext):  # type: ignore[override]
        records = context.get("payload", {}).get("records", [])
        return {"payload": {"mapped_records": records}}


class TestEventBusOrchestratorE2E:
    def test_full_pipeline_events_flow_through_bus(self):
        # 1. Set up MAC registry with dummy components
        mac_reg = MacRegistry.global_registry()
        mac_reg.register("dummy_reader", DummyReaderComponent())
        mac_reg.register("dummy_parser", DummyParserComponent())
        mac_reg.register("dummy_mapper", DummyMapperComponent())

        # 2. Set up Event Bus with subscriber
        dispatcher = EventDispatcher()
        bus_sub = InMemoryEventSubscriber()
        dispatcher.subscribe(bus_sub)

        # 3. Set up ProgressTracker with bridge
        tracker = ProgressTracker("e2e_session", total_expected_records=2)
        bridge = EventBusBridgeObserver(dispatcher)
        tracker.subscribe(bridge)
        ProgressRegistry.global_registry().register("e2e_session", tracker)

        # 4. Run the workflow
        orchestrator = ImportWorkflowOrchestrator(registry=mac_reg)
        tracker.record_session_start()

        pipeline_cfg = {
            "reader": ["dummy_reader"],
            "parser": ["dummy_parser"],
            "mapper": ["dummy_mapper"],
        }
        report = orchestrator.run_workflow(
            tenant_id="tenant_1",
            user_id="user_1",
            source="e2e_test.csv",
            pipeline_config=pipeline_cfg,
            run_id="e2e_session",
        )
        tracker.record_session_end(report.final_state.value)

        # 5. Verify events flowed through the bus
        assert report.final_state.value == "COMPLETED"

        events = bus_sub.get_events()
        assert len(events) >= 2  # At least SESSION_START and SESSION_END

        assert events[0].event_type == "SESSION_START"
        assert events[0].category == EventCategory.PROGRESS
        assert events[-1].event_type == "SESSION_END"

        # 6. Verify replay buffer
        replayed = dispatcher.replay("e2e_session")
        assert len(replayed) == len(events)
        assert replayed[0].sequence_number == 0


# ===========================================================================
# 8. Serializer
# ===========================================================================
class TestEventSerializer:
    def test_json_round_trip(self):
        original = EventEnvelope.create(
            category=EventCategory.SESSION,
            event_type="SESSION_START",
            session_id="serial_test",
            payload={"state": "RUNNING", "percentage": 42.5},
            source="session",
            sequence_number=3,
            tenant_id="t_alpha",
            institution_id="inst_beta",
            metadata={"tenant": "t1"},
        )
        json_str = EventSerializer.envelope_to_json(original)
        parsed = json.loads(json_str)
        restored = EventSerializer.envelope_from_dict(parsed)

        assert restored.category == EventCategory.SESSION
        assert restored.event_type == "SESSION_START"
        assert restored.session_id == "serial_test"
        assert restored.payload["percentage"] == 42.5
        assert restored.sequence_number == 3
        assert restored.tenant_id == "t_alpha"
        assert restored.institution_id == "inst_beta"
        assert restored.metadata["tenant"] == "t1"

    def test_progress_event_to_envelope_conversion(self):
        from apps.data_engine.progress.models import ProgressEvent, ProgressSnapshot

        snapshot = ProgressSnapshot(
            session_id="conv_test", run_id="r1", state="RUNNING",
            current_phase="Reader", overall_percentage=25.0,
            total_records_expected=100, records_processed=25,
            records_accepted=25, records_rejected=0, records_skipped=0,
            elapsed_duration_ms=1000.0, phase_durations_ms={},
            throughput_records_sec=25.0, estimated_eta_seconds=3.0,
        )
        progress_event = ProgressEvent.create(
            session_id="conv_test",
            event_type=ProgressEventType.PHASE_PROGRESS,
            snapshot=snapshot,
            message="Reading records",
        )

        envelope = EventSerializer.progress_event_to_envelope(progress_event, sequence_number=42)
        assert envelope.category == EventCategory.PROGRESS
        assert envelope.event_type == "PHASE_PROGRESS"
        assert envelope.session_id == "conv_test"
        assert envelope.sequence_number == 42
        assert envelope.source == "progress"
        assert envelope.payload["snapshot"]["records_processed"] == 25


# ===========================================================================
# 9. Zero-ORM Enforcement
# ===========================================================================
class TestZeroOrmIsolation:
    def test_events_module_has_no_django_orm_dependencies(self):
        import apps.data_engine.events.base as e_base
        import apps.data_engine.events.models as e_models
        import apps.data_engine.events.dispatcher as e_dispatcher
        import apps.data_engine.events.subscribers as e_subscribers
        import apps.data_engine.events.registry as e_registry
        import apps.data_engine.events.serializers as e_serializers

        forbidden_patterns = ["django.db", "models.Model", "QuerySet", "transaction.atomic"]

        for mod in (e_base, e_models, e_dispatcher, e_subscribers, e_registry, e_serializers):
            with open(mod.__file__, "r", encoding="utf-8") as f:
                content = f.read()
                for pattern in forbidden_patterns:
                    assert pattern not in content, (
                        f"Found forbidden pattern '{pattern}' in {mod.__file__}"
                    )
