# apps/data_engine/integration/contracts.py
"""Abstract contracts/interfaces for the ERP Integration Layer components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .dto import BatchPersistenceResult, PersistenceResult


class BaseEntityMapper(ABC):
    """Abstract contract for translating records into normalized entity maps."""

    @abstractmethod
    def map_record(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert a record dictionary into the target entity attributes dictionary."""
        raise NotImplementedError  # pragma: no cover


class BasePersistenceAdapter(ABC):
    """Abstract contract for persisting normalized entity records into the ERP."""

    @abstractmethod
    def persist(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> PersistenceResult:
        """Persist a single record and return its individual result."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def persist_batch(self, records: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> BatchPersistenceResult:
        """Persist a list of records in a single batch."""
        raise NotImplementedError  # pragma: no cover


class BaseTransactionManager(ABC):
    """Abstract contract for managing transaction boundaries."""

    @abstractmethod
    def begin(self) -> None:
        """Begin transaction."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def commit(self) -> None:
        """Commit transaction."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def rollback(self) -> None:
        """Rollback transaction."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def __enter__(self) -> "BaseTransactionManager":
        """Enter transaction context."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit transaction context, committing if no exception, rolling back otherwise."""
        raise NotImplementedError  # pragma: no cover


class BaseIntegrationService(ABC):
    """Abstract contract for coordinating the high-level integration workflow."""

    @abstractmethod
    def integrate(
        self,
        entity_name: str,
        records: List[Dict[str, Any]],
        tenant_id: str,
        user_id: str,
        run_id: str,
        is_dry_run: bool = False,
    ) -> BatchPersistenceResult:
        """Translate source records to entity dictionaries and persist them inside a transaction."""
        raise NotImplementedError  # pragma: no cover
