# apps/data_engine/events/base.py
"""Abstract contracts for the Real-Time Event Bus & Notification Framework.

Defines ``BaseEventSubscriber`` and ``BaseEventDispatcher`` interfaces that
enforce Dependency Inversion across the event distribution layer.  Concrete
implementations (in-memory, Channels, Redis, etc.) must reside in separate
modules and never introduce Django ORM dependencies.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Set

from .models import EventCategory, EventEnvelope


class BaseEventSubscriber(ABC):
    """Abstract interface for consumers of the MAC Event Bus.

    Implementations may include WebSocket broadcasters, SSE stream writers,
    Redis publishers, in-memory collectors, or logging sinks.
    """

    @abstractmethod
    def on_event(self, envelope: EventEnvelope) -> None:
        """Receive and process an event envelope from the Event Bus."""
        raise NotImplementedError

    def accepts(self, category: EventCategory) -> bool:
        """Return ``True`` if this subscriber wants events of the given category.

        The default implementation accepts all categories.  Override to
        implement subscriber-level filtering.
        """
        return True


class BaseEventDispatcher(ABC):
    """Abstract contract for the central event distribution bus."""

    @abstractmethod
    def publish(self, envelope: EventEnvelope) -> None:
        """Publish an event envelope to all eligible subscribers."""
        raise NotImplementedError

    @abstractmethod
    def subscribe(
        self,
        subscriber: "BaseEventSubscriber",
        categories: Optional[Set[EventCategory]] = None,
    ) -> None:
        """Register a subscriber, optionally filtering by event categories."""
        raise NotImplementedError

    @abstractmethod
    def unsubscribe(self, subscriber: "BaseEventSubscriber") -> None:
        """Remove a previously registered subscriber."""
        raise NotImplementedError

    @abstractmethod
    def replay(
        self,
        session_id: str,
        since_sequence: int = 0,
    ) -> List[EventEnvelope]:
        """Return buffered envelopes for *session_id* with ``sequence_number >= since_sequence``."""
        raise NotImplementedError
