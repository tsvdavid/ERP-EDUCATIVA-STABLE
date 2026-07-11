# apps/data_engine/persistence/base.py
"""Abstract contracts for the Transactional Persistence Adapter.

Defines interfaces for:
- ``BaseRepository``: Abstract contract for entity-specific data persistence in Django ORM.
- ``BasePersistenceExecutor``: Abstract contract for executing persistence operations safely.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .models import EntityPersistenceResult, PersistenceContext, TransactionResult


class BaseRepository(ABC):
    """Abstract contract for entity-specific persistence inside Django ORM.

    Subclasses must define `entity_name` and implement all lifecycle methods
    (`create`, `update`, `find_existing`, `resolve_dependencies`, `validate_constraints`).
    """

    entity_name: str = ""

    @abstractmethod
    def create(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> EntityPersistenceResult:
        """Create a new database record from the payload within the given tenant context.

        Args:
            payload: Data fields for creating the record.
            context: The multi-tenant `PersistenceContext` with resolved dependencies.

        Returns:
            `EntityPersistenceResult` detailing success, ORM ID, and `created=True`.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def update(
        self,
        existing_instance: Any,
        payload: Dict[str, Any],
        context: PersistenceContext,
    ) -> EntityPersistenceResult:
        """Update an existing database record with new payload fields.

        Args:
            existing_instance: The existing Django model instance found via `find_existing`.
            payload: New data fields to update.
            context: The multi-tenant `PersistenceContext`.

        Returns:
            `EntityPersistenceResult` detailing success, ORM ID, and `created=False`.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def find_existing(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Optional[Any]:
        """Locate an existing database record by natural or candidate keys.

        Args:
            payload: Data fields containing unique keys (e.g., code, RUC, cedula).
            context: The multi-tenant `PersistenceContext`.

        Returns:
            Existing Django model instance if found, else None.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def resolve_dependencies(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Dict[str, Any]:
        """Extract or verify required foreign key references from context.resolved_dependencies.

        Args:
            payload: Data fields containing reference IDs.
            context: The multi-tenant `PersistenceContext`.

        Returns:
            Dictionary mapping model foreign key field names to resolved ORM instances or PKs.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def validate_constraints(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> List[str]:
        """Validate domain logic and schema constraints prior to executing ORM write.

        Args:
            payload: Data fields to validate.
            context: The multi-tenant `PersistenceContext`.

        Returns:
            List of error string messages if constraints are violated, else empty list.
        """
        raise NotImplementedError  # pragma: no cover


class BasePersistenceExecutor(ABC):
    """Abstract contract for executing persistence steps with transaction control."""

    @abstractmethod
    def execute_persistence(
        self, step: Any, context: Any
    ) -> TransactionResult:
        """Execute the persistence of a step within a secure transaction boundary.

        Args:
            step: The step or node object to persist.
            context: Shared execution context.

        Returns:
            Consolidated `TransactionResult`.
        """
        raise NotImplementedError  # pragma: no cover


__all__ = [
    "BaseRepository",
    "BasePersistenceExecutor",
]
