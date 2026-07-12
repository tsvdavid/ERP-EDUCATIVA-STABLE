# apps/data_engine/events/subscribers.py
"""Standard subscriber implementations for the MAC Event Bus.

Provides ready-to-use consumers:
- ``InMemoryEventSubscriber``: Collects events in memory (testing / debugging).
- ``CallbackEventSubscriber``: Forwards events to a callback function.
- ``LoggingEventSubscriber``: Writes structured logs via Python ``logging``.
- ``FilteredEventSubscriber``: Decorator that adds fine-grained filtering
  (by category, event_type, or session_id) on top of another subscriber.
"""

import logging
import threading
from typing import Callable, List, Optional, Set

from .base import BaseEventSubscriber
from .models import EventCategory, EventEnvelope


class InMemoryEventSubscriber(BaseEventSubscriber):
    """Thread-safe subscriber that retains all received envelopes in memory.

    Useful for unit testing, debugging, or querying historical events.
    """

    def __init__(self) -> None:
        self._events: List[EventEnvelope] = []
        self._lock = threading.Lock()

    def on_event(self, envelope: EventEnvelope) -> None:
        with self._lock:
            self._events.append(envelope)

    def get_events(self) -> List[EventEnvelope]:
        """Return a copy of the chronological event history."""
        with self._lock:
            return list(self._events)

    def get_events_by_category(self, category: EventCategory) -> List[EventEnvelope]:
        """Return events filtered by a specific category."""
        with self._lock:
            return [e for e in self._events if e.category == category]

    def get_events_by_session(self, session_id: str) -> List[EventEnvelope]:
        """Return events filtered by a specific session ID."""
        with self._lock:
            return [e for e in self._events if e.session_id == session_id]

    def clear(self) -> None:
        """Remove all stored events."""
        with self._lock:
            self._events.clear()


class CallbackEventSubscriber(BaseEventSubscriber):
    """Subscriber that forwards each event to a user-provided callback function.

    Serves as a universal bridge to any external transport (WebSocket, SSE,
    Redis Pub/Sub, Webhooks, etc.).

    Parameters
    ----------
    callback_fn : Callable[[EventEnvelope], None]
        Function invoked with each received ``EventEnvelope``.
    """

    def __init__(self, callback_fn: Callable[[EventEnvelope], None]) -> None:
        if not callable(callback_fn):
            raise TypeError("callback_fn must be a callable")
        self._callback_fn = callback_fn

    def on_event(self, envelope: EventEnvelope) -> None:
        self._callback_fn(envelope)


class LoggingEventSubscriber(BaseEventSubscriber):
    """Subscriber that writes structured event logs via Python ``logging``.

    Parameters
    ----------
    logger : Optional[logging.Logger]
        Logger instance (defaults to ``apps.data_engine.events``).
    level : int
        Logging level (defaults to ``logging.INFO``).
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        level: int = logging.INFO,
    ) -> None:
        self._logger = logger or logging.getLogger("apps.data_engine.events")
        self._level = level

    def on_event(self, envelope: EventEnvelope) -> None:
        self._logger.log(
            self._level,
            "[EventBus] [%s] [%s/%s] seq=%d session=%s",
            envelope.category.value,
            envelope.source,
            envelope.event_type,
            envelope.sequence_number,
            envelope.session_id,
        )


class FilteredEventSubscriber(BaseEventSubscriber):
    """Decorator subscriber that applies fine-grained filters before delegating.

    Wraps any ``BaseEventSubscriber`` and only forwards events that match
    the configured filter criteria.

    Parameters
    ----------
    inner : BaseEventSubscriber
        The underlying subscriber to forward matching events to.
    categories : Optional[Set[EventCategory]]
        If provided, only events with a matching category are forwarded.
    event_types : Optional[Set[str]]
        If provided, only events with a matching ``event_type`` are forwarded.
    session_ids : Optional[Set[str]]
        If provided, only events from matching sessions are forwarded.
    """

    def __init__(
        self,
        inner: BaseEventSubscriber,
        categories: Optional[Set[EventCategory]] = None,
        event_types: Optional[Set[str]] = None,
        session_ids: Optional[Set[str]] = None,
    ) -> None:
        if not isinstance(inner, BaseEventSubscriber):
            raise TypeError("inner must implement BaseEventSubscriber")
        self._inner = inner
        self._categories = categories
        self._event_types = event_types
        self._session_ids = session_ids

    def on_event(self, envelope: EventEnvelope) -> None:
        if self._categories and envelope.category not in self._categories:
            return
        if self._event_types and envelope.event_type not in self._event_types:
            return
        if self._session_ids and envelope.session_id not in self._session_ids:
            return
        self._inner.on_event(envelope)

    def accepts(self, category: EventCategory) -> bool:
        if self._categories:
            return category in self._categories
        return True
