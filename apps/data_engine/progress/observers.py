# apps/data_engine/progress/observers.py
"""Standard observer implementations (`BaseProgressObserver`).

Provides versatile built-in observers for the real-time monitoring framework:
- `CallbackProgressObserver`: Forwards events to a custom callback function (e.g. for WebSockets/SSE/APIs).
- `LoggingProgressObserver`: Outputs formatted progress milestones to Python `logging`.
- `InMemoryProgressObserver`: Retains an in-memory chronological trace (`List[ProgressEvent]`) of milestones.
"""

import logging
import threading
from typing import Callable, List, Optional

from .base import BaseProgressObserver
from .models import ProgressEvent


class CallbackProgressObserver(BaseProgressObserver):
    """Observer that forwards emitted progress events directly to a user-provided callback function.

    Parameters
    ----------
    callback_fn: Callable[[ProgressEvent], None]
        Function invoked whenever a new `ProgressEvent` is received.
    """

    def __init__(self, callback_fn: Callable[[ProgressEvent], None]):
        if not callable(callback_fn):
            raise TypeError("callback_fn must be a callable function")
        self._callback_fn = callback_fn

    def on_progress(self, event: ProgressEvent) -> None:
        """Invoke the registered callback with the received progress event."""
        self._callback_fn(event)


class LoggingProgressObserver(BaseProgressObserver):
    """Observer that logs real-time progress events using standard Python logging.

    Parameters
    ----------
    logger: Optional[logging.Logger]
        Logger instance to write to (defaults to a logger named 'apps.data_engine.progress').
    level: int
        Logging level (defaults to `logging.INFO`).
    """

    def __init__(self, logger: Optional[logging.Logger] = None, level: int = logging.INFO):
        self._logger = logger or logging.getLogger("apps.data_engine.progress")
        self._level = level

    def on_progress(self, event: ProgressEvent) -> None:
        """Log the progress event milestone using the configured logger."""
        self._logger.log(
            self._level,
            "[%s] [%s] %s (overall=%s%%, throughput=%s rec/s, eta=%ss)",
            event.session_id,
            event.event_type.value,
            event.message,
            event.snapshot.overall_percentage,
            event.snapshot.throughput_records_sec,
            event.snapshot.estimated_eta_seconds,
        )


class InMemoryProgressObserver(BaseProgressObserver):
    """Thread-safe observer that collects and retains all received progress events in memory.

    Useful for unit testing, debugging, or querying historical milestones of a session.
    """

    def __init__(self):
        self._history: List[ProgressEvent] = []
        self._lock = threading.Lock()

    def on_progress(self, event: ProgressEvent) -> None:
        """Append the received progress event to the internal thread-safe history list."""
        with self._lock:
            self._history.append(event)

    def get_history(self) -> List[ProgressEvent]:
        """Return a copy of the chronological progress event history."""
        with self._lock:
            return list(self._history)

    def clear(self) -> None:
        """Clear all stored progress events from memory."""
        with self._lock:
            self._history.clear()
