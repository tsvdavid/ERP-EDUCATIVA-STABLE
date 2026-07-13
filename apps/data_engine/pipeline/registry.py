# apps/data_engine/pipeline/registry.py
"""Central, thread-safe registry to store and retrieve PipelineRuntime instances."""

import threading
from typing import Dict, Optional

from apps.data_engine.pipeline.runtime import PipelineRuntime


class PipelineRuntimeRegistry:
    """Thread-safe singleton registry administering active PipelineRuntime instances."""

    _instance: Optional["PipelineRuntimeRegistry"] = None
    _singleton_lock = threading.Lock()

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runtimes: Dict[str, PipelineRuntime] = {}

    @classmethod
    def global_registry(cls) -> "PipelineRuntimeRegistry":
        """Return the global thread-safe singleton instance of PipelineRuntimeRegistry."""
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register(self, pipeline_id: str, runtime: PipelineRuntime) -> None:
        """Register an active PipelineRuntime instance under the specified ID."""
        if not pipeline_id:
            raise ValueError("Pipeline ID cannot be empty.")
        if not isinstance(runtime, PipelineRuntime):
            raise TypeError("Value must be an instance of PipelineRuntime.")
        with self._lock:
            self._runtimes[pipeline_id] = runtime

    def get(self, pipeline_id: str) -> PipelineRuntime:
        """Retrieve a registered PipelineRuntime by its ID."""
        with self._lock:
            if pipeline_id not in self._runtimes:
                raise KeyError(f"Pipeline runtime '{pipeline_id}' not found in registry.")
            return self._runtimes[pipeline_id]

    def remove(self, pipeline_id: str) -> None:
        """Remove a PipelineRuntime from the registry."""
        with self._lock:
            self._runtimes.pop(pipeline_id, None)

    def clear(self) -> None:
        """Clear all registered runtimes."""
        with self._lock:
            self._runtimes.clear()
