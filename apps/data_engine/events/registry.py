# apps/data_engine/events/registry.py
"""Thread-safe global EventBus registry (Singleton).

Provides a centralized access point to the global ``EventDispatcher``
instance, following the same Singleton pattern used by ``MacRegistry``
and ``ProgressRegistry`` throughout the MAC codebase.
"""

import threading
from typing import Optional

from .dispatcher import EventDispatcher


class EventBusRegistry:
    """Thread-safe Singleton registry for the global Event Bus dispatcher."""

    _instance: Optional["EventBusRegistry"] = None
    _singleton_lock = threading.Lock()

    def __init__(self) -> None:
        self._dispatcher: Optional[EventDispatcher] = None
        self._lock = threading.Lock()

    @classmethod
    def global_registry(cls) -> "EventBusRegistry":
        """Return the global singleton instance of the ``EventBusRegistry``."""
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_dispatcher(self) -> EventDispatcher:
        """Return the global ``EventDispatcher``, creating it lazily if needed."""
        if self._dispatcher is None:
            with self._lock:
                if self._dispatcher is None:
                    self._dispatcher = EventDispatcher()
        return self._dispatcher

    def reset(self) -> None:
        """Reset the global dispatcher (primarily for test cleanup)."""
        with self._lock:
            if self._dispatcher is not None:
                self._dispatcher.clear()
            self._dispatcher = None
