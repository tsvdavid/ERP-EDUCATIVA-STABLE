# apps/data_engine/integration/registry.py
"""Thread-safe global singleton registry for ERP persistence adapters."""

import threading
from typing import Dict
from .contracts import BasePersistenceAdapter
from .exceptions import AdapterNotFoundError


class IntegrationRegistry:
    """Singleton directory for registering and resolving ERP persistence adapters."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "IntegrationRegistry":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._adapters = {}
                cls._instance._adapters_lock = threading.Lock()
        return cls._instance

    @classmethod
    def global_registry(cls) -> "IntegrationRegistry":
        """Return the global singleton instance of the IntegrationRegistry."""
        return cls()

    def register(self, entity_name: str, adapter: BasePersistenceAdapter, overwrite: bool = True) -> None:
        """Register a persistence adapter for a specific entity name."""
        with self._adapters_lock:
            key = entity_name.strip().lower()
            if key in self._adapters and not overwrite:
                raise ValueError(f"Persistence adapter for {entity_name} is already registered.")
            self._adapters[key] = adapter

    def unregister(self, entity_name: str) -> None:
        """Unregister a persistence adapter for an entity name."""
        with self._adapters_lock:
            key = entity_name.strip().lower()
            if key in self._adapters:
                del self._adapters[key]

    def get(self, entity_name: str) -> BasePersistenceAdapter:
        """Retrieve a persistence adapter by entity name."""
        with self._adapters_lock:
            key = entity_name.strip().lower()
            if key not in self._adapters:
                raise AdapterNotFoundError(f"No persistence adapter registered for entity: {entity_name}")
            return self._adapters[key]

    def clear(self) -> None:
        """Clear all registered adapters."""
        with self._adapters_lock:
            self._adapters.clear()

    def exists(self, entity_name: str) -> bool:
        """Check if an adapter is registered for the entity name."""
        with self._adapters_lock:
            key = entity_name.strip().lower()
            return key in self._adapters
