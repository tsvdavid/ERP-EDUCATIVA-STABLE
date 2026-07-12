# apps/data_engine/transformations/registry.py
"""Thread-safe TransformationRegistry administering transformation classes and instances."""

import threading
from typing import Dict, List, Optional, Union, Type

from .base import BaseTransformation
from .exceptions import TransformationException


class TransformationRegistry:
    """Singleton thread-safe registry mapping transformation names to instances or classes."""

    _instance: Optional["TransformationRegistry"] = None
    _singleton_lock = threading.Lock()

    def __init__(self) -> None:
        self._items: Dict[str, Union[BaseTransformation, Type[BaseTransformation]]] = {}
        self._lock = threading.Lock()

    @classmethod
    def global_registry(cls) -> "TransformationRegistry":
        """Return the global singleton TransformationRegistry instance."""
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

    def register(
        self,
        name: str,
        transformation: Union[BaseTransformation, Type[BaseTransformation]],
    ) -> None:
        """Register a transformation instance or class under a unique name key."""
        if not (
            isinstance(transformation, BaseTransformation)
            or (isinstance(transformation, type) and issubclass(transformation, BaseTransformation))
        ):
            raise TypeError(f"{transformation} must be a BaseTransformation instance or subclass")
        with self._lock:
            self._items[name.lower()] = transformation

    def get(self, name: str) -> Union[BaseTransformation, Type[BaseTransformation]]:
        """Retrieve the registered transformation or class for the given name."""
        key = name.lower()
        with self._lock:
            item = self._items.get(key)
        if item is None:
            raise TransformationException(f"Transformation '{name}' is not registered.")
        return item

    def list_names(self) -> List[str]:
        """Return a sorted list of all registered transformation identifiers."""
        with self._lock:
            return sorted(self._items.keys())
