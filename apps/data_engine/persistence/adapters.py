# apps/data_engine/persistence/adapters.py
"""Repository resolver and adapter utilities for the Transactional Persistence Adapter.

Defines:
- ``RepositoryResolver``: Bridges `LoadNode.entity_name` to registered concrete repositories.
"""

from typing import Any

from apps.data_engine.components.loaders.models import LoadNode
from .base import BaseRepository
from .registry import RepositoryRegistry


class RepositoryResolver:
    """Resolves target repositories for `LoadNode` instances based on `entity_name`."""

    @staticmethod
    def resolve(entity_name: str) -> BaseRepository:
        """Resolve a repository instance for the given entity name.

        Args:
            entity_name: Name of the entity type (e.g., "Institution").

        Returns:
            Registered `BaseRepository` instance.

        Raises:
            KeyError: If no repository is registered for `entity_name`.
            ValueError: If `entity_name` is empty or non-string.
        """
        if not entity_name or not isinstance(entity_name, str):
            raise ValueError(f"Invalid entity_name for resolution: '{entity_name}'")

        return RepositoryRegistry.get(entity_name)

    @classmethod
    def resolve_for_node(cls, node: Any) -> BaseRepository:
        """Resolve a repository instance for a specific `LoadNode`.

        Args:
            node: The `LoadNode` or node-like object with an `entity_name` attribute.

        Returns:
            Registered `BaseRepository` instance.

        Raises:
            TypeError: If `node` lacks `entity_name`.
            KeyError: If no repository is registered for `node.entity_name`.
        """
        if not hasattr(node, "entity_name"):
            raise TypeError(
                f"Cannot resolve repository: node object {node} lacks 'entity_name' attribute"
            )
        return cls.resolve(node.entity_name)


__all__ = [
    "RepositoryResolver",
]
