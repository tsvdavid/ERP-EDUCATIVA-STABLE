# apps/data_engine/persistence/registry.py
"""Centralized repository management for the Transactional Persistence Adapter.

Defines:
- ``RepositoryRegistry``: Singleton/thread-safe registry mapping entity names to `BaseRepository` implementations.
"""

from typing import Dict, List, Optional, Type, Union

from .base import BaseRepository


class RepositoryRegistry:
    """Registry managing concrete repository implementations for domain entities.

    Enforces that every entity type processed by the Execution Engine has a corresponding
    concrete repository registered before execution attempts occur.
    """

    _registry: Dict[str, BaseRepository] = {}

    @classmethod
    def register(cls, repository: Union[BaseRepository, Type[BaseRepository]]) -> None:
        """Register a repository instance or class for an entity type.

        Args:
            repository: An instance or subclass of `BaseRepository`.

        Raises:
            TypeError: If repository does not inherit from `BaseRepository`.
            ValueError: If `entity_name` is empty.
        """
        if isinstance(repository, type):
            if not issubclass(repository, BaseRepository):
                raise TypeError(
                    f"Repository class {repository} must inherit from BaseRepository"
                )
            instance = repository()
        elif isinstance(repository, BaseRepository):
            instance = repository
        else:
            raise TypeError(
                f"Expected BaseRepository instance or subclass, got {type(repository)}"
            )

        entity_name = instance.entity_name
        if not entity_name:
            raise ValueError("Repository entity_name attribute cannot be empty")

        cls._registry[entity_name] = instance

    @classmethod
    def get(cls, entity_name: str) -> BaseRepository:
        """Retrieve the registered repository instance for a given entity name.

        Args:
            entity_name: The target entity type name (e.g., "Institution").

        Returns:
            Registered `BaseRepository` instance.

        Raises:
            KeyError: If no repository is registered for `entity_name`.
        """
        if entity_name not in cls._registry:
            raise KeyError(
                f"No repository registered for entity type '{entity_name}'. "
                f"Available entities: {list(cls._registry.keys())}"
            )
        return cls._registry[entity_name]

    @classmethod
    def is_registered(cls, entity_name: str) -> bool:
        """Check whether a repository is registered for `entity_name`."""
        return entity_name in cls._registry

    @classmethod
    def all_entities(cls) -> List[str]:
        """Return a list of all registered entity names."""
        return list(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered repositories (primarily used for testing/isolation)."""
        cls._registry.clear()


__all__ = [
    "RepositoryRegistry",
]
