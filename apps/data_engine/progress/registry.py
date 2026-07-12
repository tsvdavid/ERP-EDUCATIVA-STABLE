# apps/data_engine/progress/registry.py
"""Thread-safe ProgressRegistry (`ProgressTracker` centralized directory).

Provides a global, in-memory directory mapping active `session_id`s to their corresponding
`ProgressTracker` instances. Enables O(1) real-time state and metrics queries from API endpoints,
CLI commands, or background tasks without coupling to database lookups or ORM models.
"""

import threading
from typing import Dict, List, Optional

from .base import BaseProgressTracker


class ProgressRegistry:
    """Thread-safe centralized registry for active session progress trackers."""

    _instance: Optional["ProgressRegistry"] = None
    _singleton_lock = threading.Lock()

    def __init__(self):
        self._trackers: Dict[str, BaseProgressTracker] = {}
        self._lock = threading.Lock()

    @classmethod
    def global_registry(cls) -> "ProgressRegistry":
        """Return the global singleton instance of the ProgressRegistry."""
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register(self, session_id: str, tracker: BaseProgressTracker) -> None:
        """Register an active progress tracker under the specified session ID."""
        if not session_id:
            raise ValueError("session_id must be non-empty")
        if not isinstance(tracker, BaseProgressTracker):
            raise TypeError("tracker must implement BaseProgressTracker")
        with self._lock:
            self._trackers[session_id] = tracker

    def unregister(self, session_id: str) -> Optional[BaseProgressTracker]:
        """Remove and return the progress tracker associated with the given session ID."""
        with self._lock:
            return self._trackers.pop(session_id, None)

    def get(self, session_id: str) -> Optional[BaseProgressTracker]:
        """Retrieve the active progress tracker for the given session ID, or None if not found."""
        with self._lock:
            return self._trackers.get(session_id)

    def list_active_sessions(self) -> List[str]:
        """Return a list of all currently registered active session IDs."""
        with self._lock:
            return list(self._trackers.keys())

    def clear(self) -> None:
        """Clear all registered progress trackers from the global registry."""
        with self._lock:
            self._trackers.clear()
