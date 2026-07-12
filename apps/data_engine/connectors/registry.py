# apps/data_engine/connectors/registry.py
"""Thread-safe ConnectorRegistry administering external connector classes."""

import threading
from typing import Dict, List, Optional, Type

from .base import BaseConnector
from .exceptions import UnsupportedConnectorException


class ConnectorRegistry:
    """Singleton thread-safe registry mapping connector types to concrete implementations."""

    _instance: Optional["ConnectorRegistry"] = None
    _singleton_lock = threading.Lock()

    def __init__(self) -> None:
        self._connectors: Dict[str, Type[BaseConnector]] = {}
        self._lock = threading.Lock()

    @classmethod
    def global_registry(cls) -> "ConnectorRegistry":
        """Return the global singleton ConnectorRegistry instance."""
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_global_registry(cls) -> None:
        """Reset the global singleton registry (for isolated unit testing)."""
        with cls._singleton_lock:
            cls._instance = None

    def register(self, connector_type: str, connector_cls: Type[BaseConnector]) -> None:
        """Register a concrete BaseConnector class under a unique type key.

        Parameters
        ----------
        connector_type : str
            Unique string identifier (e.g., 'csv', 'rest', 'sql').
        connector_cls : Type[BaseConnector]
            Class inheriting from `BaseConnector`.
        """
        if not issubclass(connector_cls, BaseConnector):
            raise TypeError(f"{connector_cls} must inherit from BaseConnector")
        with self._lock:
            self._connectors[connector_type.lower()] = connector_cls

    def get_connector_class(self, connector_type: str) -> Type[BaseConnector]:
        """Retrieve the registered class for the given connector type."""
        key = connector_type.lower()
        with self._lock:
            cls = self._connectors.get(key)
        if cls is None:
            raise UnsupportedConnectorException(f"Connector type '{connector_type}' is not registered.")
        return cls

    def list_supported_connectors(self) -> List[str]:
        """Return a sorted list of all registered connector type identifiers."""
        with self._lock:
            return sorted(self._connectors.keys())
