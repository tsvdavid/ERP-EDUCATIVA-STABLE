# apps/data_engine/jobs/registry.py
"""JobRegistry — Dependency Injection & Adapter Registry for Background Jobs (TAREA 24).

Allows decoupling the high-level `JobManager` from concrete storage (`BaseJobStore`),
enqueuing (`BaseJobQueue`), and worker execution (`BaseJobRunner`) adapters.
"""

import threading
from typing import Optional, Type

from .contracts import BaseJobQueue, BaseJobRunner, BaseJobStore
from .exceptions import JobException


class JobRegistry:
    """Registry managing DI adapters for background job management."""
    _instance: Optional["JobRegistry"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._store: Optional[BaseJobStore] = None
        self._queue: Optional[BaseJobQueue] = None
        self._runner: Optional[BaseJobRunner] = None

    @classmethod
    def global_registry(cls) -> "JobRegistry":
        """Return the singleton global JobRegistry instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = JobRegistry()
        return cls._instance

    @classmethod
    def reset_global_registry(cls) -> None:
        """Reset and clear the global registry singleton (useful for isolated testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.clear()
            cls._instance = None

    def register_store(self, store: BaseJobStore) -> None:
        """Register the storage adapter used for persisting job state records."""
        if not isinstance(store, BaseJobStore):
            raise TypeError(f"Expected BaseJobStore instance, got {type(store).__name__}")
        self._store = store

    def get_store(self) -> BaseJobStore:
        """Resolve the registered BaseJobStore adapter or lazy-load the default InMemory store."""
        if self._store is None:
            from .adapters import InMemoryJobStore
            self._store = InMemoryJobStore()
        return self._store

    def register_queue(self, queue: BaseJobQueue) -> None:
        """Register the queue/broker adapter used for enqueuing jobs."""
        if not isinstance(queue, BaseJobQueue):
            raise TypeError(f"Expected BaseJobQueue instance, got {type(queue).__name__}")
        self._queue = queue

    def get_queue(self) -> BaseJobQueue:
        """Resolve the registered BaseJobQueue adapter or lazy-load the default InMemory queue."""
        if self._queue is None:
            from .adapters import InMemoryJobQueue
            self._queue = InMemoryJobQueue()
        return self._queue

    def register_runner(self, runner: BaseJobRunner) -> None:
        """Register the runner adapter responsible for executing jobs inside workers."""
        if not isinstance(runner, BaseJobRunner):
            raise TypeError(f"Expected BaseJobRunner instance, got {type(runner).__name__}")
        self._runner = runner

    def get_runner(self) -> BaseJobRunner:
        """Resolve the registered BaseJobRunner adapter."""
        if self._runner is None:
            from .manager import JobManager
            self._runner = JobManager.global_instance()
        return self._runner

    def clear(self) -> None:
        """Clear all registered adapters."""
        self._store = None
        self._queue = None
        self._runner = None
