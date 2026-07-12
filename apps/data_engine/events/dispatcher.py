# apps/data_engine/events/dispatcher.py
"""Concrete Event Bus dispatcher and ProgressTracker bridge.

``EventDispatcher`` is the thread-safe central hub that distributes
``EventEnvelope`` instances to registered subscribers with optional
category-level filtering and per-session replay buffering.

``EventBusBridgeObserver`` adapts the existing ``BaseProgressObserver``
contract from TAREA 20 to the Event Bus without modifying any code in
the progress module.
"""

import threading
from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Optional, Set

from apps.data_engine.progress.base import BaseProgressObserver
from apps.data_engine.progress.models import ProgressEvent

from .base import BaseEventDispatcher, BaseEventSubscriber
from .models import EventCategory, EventEnvelope


class EventDispatcher(BaseEventDispatcher):
    """Thread-safe in-memory event bus with category filtering and replay buffer.

    Parameters
    ----------
    max_replay_buffer_size : int
        Maximum number of envelopes retained per session in the replay buffer.
        Oldest envelopes are discarded when the limit is exceeded.
    """

    def __init__(self, max_replay_buffer_size: int = 1000):
        if max_replay_buffer_size < 0:
            raise ValueError("max_replay_buffer_size must be non-negative")
        self._max_buffer = max_replay_buffer_size
        self._lock = threading.Lock()

        # subscriber -> optional set of accepted categories (None = all)
        self._subscribers: Dict[BaseEventSubscriber, Optional[Set[EventCategory]]] = {}

        # session_id -> deque of envelopes (replay buffer with automatic cap)
        self._buffers: Dict[str, Deque[EventEnvelope]] = {}

        # session_id -> next sequence number (monotonic counter)
        self._sequences: Dict[str, int] = defaultdict(int)

    def publish(self, envelope: EventEnvelope) -> None:
        """Publish an event envelope to all eligible subscribers and buffer it."""
        with self._lock:
            # Buffer the envelope for future replay (deque auto-discards oldest)
            if envelope.session_id not in self._buffers:
                self._buffers[envelope.session_id] = deque(maxlen=self._max_buffer)
            self._buffers[envelope.session_id].append(envelope)

            # Snapshot subscribers to release the lock before invoking callbacks
            subs_snapshot = list(self._subscribers.items())

        # Deliver outside the lock to avoid deadlocks with subscriber code
        for subscriber, categories in subs_snapshot:
            if categories is not None and envelope.category not in categories:
                continue
            if not subscriber.accepts(envelope.category):
                continue
            try:
                subscriber.on_event(envelope)
            except Exception:
                # Individual subscriber failures must not crash the bus
                pass

    def subscribe(
        self,
        subscriber: BaseEventSubscriber,
        categories: Optional[Set[EventCategory]] = None,
    ) -> None:
        """Register a subscriber with optional category-level filtering."""
        if not isinstance(subscriber, BaseEventSubscriber):
            raise TypeError("subscriber must implement BaseEventSubscriber")
        with self._lock:
            self._subscribers[subscriber] = categories

    def unsubscribe(self, subscriber: BaseEventSubscriber) -> None:
        """Remove a previously registered subscriber."""
        with self._lock:
            self._subscribers.pop(subscriber, None)

    def replay(
        self,
        session_id: str,
        since_sequence: int = 0,
    ) -> List[EventEnvelope]:
        """Return buffered envelopes for *session_id* with ``sequence_number >= since_sequence``."""
        with self._lock:
            buf = self._buffers.get(session_id, deque())
            return [e for e in buf if e.sequence_number >= since_sequence]

    def next_sequence(self, session_id: str) -> int:
        """Atomically increment and return the next sequence number for *session_id*."""
        with self._lock:
            seq = self._sequences[session_id]
            self._sequences[session_id] = seq + 1
            return seq

    def clear_session(self, session_id: str) -> None:
        """Remove replay buffer and sequence counter for a finished session."""
        with self._lock:
            self._buffers.pop(session_id, None)
            self._sequences.pop(session_id, None)

    def clear(self) -> None:
        """Reset all internal state (subscribers, buffers, sequences)."""
        with self._lock:
            self._subscribers.clear()
            self._buffers.clear()
            self._sequences.clear()


class EventBusBridgeObserver(BaseProgressObserver):
    """Bridge between the TAREA 20 ``ProgressTracker`` Observer pattern and the Event Bus.

    Converts each ``ProgressEvent`` into an ``EventEnvelope`` with
    ``category=PROGRESS`` and publishes it to the injected ``EventDispatcher``.

    This class allows the Event Bus to receive all progress events without
    modifying any code in the ``progress/`` package (TAREA 20).

    Parameters
    ----------
    dispatcher : EventDispatcher
        The event bus to publish converted envelopes to.
    """

    def __init__(self, dispatcher: EventDispatcher):
        if not isinstance(dispatcher, BaseEventDispatcher):
            raise TypeError("dispatcher must implement BaseEventDispatcher")
        self._dispatcher = dispatcher

    def on_progress(self, event: ProgressEvent) -> None:
        """Convert a ``ProgressEvent`` to an ``EventEnvelope`` and publish it."""
        seq = self._dispatcher.next_sequence(event.session_id)
        envelope = EventEnvelope.create(
            category=EventCategory.PROGRESS,
            event_type=event.event_type.value,
            session_id=event.session_id,
            payload=event.to_dict(),
            source="progress",
            sequence_number=seq,
            metadata=dict(event.metadata) if event.metadata else {},
        )
        self._dispatcher.publish(envelope)
