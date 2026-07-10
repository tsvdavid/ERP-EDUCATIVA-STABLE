# apps/data_engine/core/registry.py
"""Registry for MAC components.

Components are simple objects that expose an ``execute`` method. The registry
stores them by a string key and provides lookup with proper error handling.
"""

from typing import Dict, Any, List

from .exceptions import ComponentNotFoundError


class MacRegistry:
    """Container for MAC components.

    Provides a global singleton via :meth:`global_registry`. Components can be
    registered, retrieved, and listed.
    """

    _global_instance: "MacRegistry | None" = None

    def __init__(self) -> None:
        self._components: Dict[str, Any] = {}

    @classmethod
    def global_registry(cls) -> "MacRegistry":
        if cls._global_instance is None:
            cls._global_instance = cls()
        return cls._global_instance

    def register(self, name: str, component: Any) -> None:
        """Register *component* under *name*.

        Overwrites any existing entry with the same name.
        """
        self._components[name] = component

    def get(self, name: str) -> Any:
        """Retrieve component by *name*.

        Raises ``ComponentNotFoundError`` if the name is unknown.
        """
        try:
            return self._components[name]
        except KeyError as exc:
            raise ComponentNotFoundError(f"Component '{name}' not found") from exc

    def list_components(self) -> List[str]:
        """Return a list of all registered component names."""
        return list(self._components.keys())
