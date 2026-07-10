# apps/data_engine/components/staging/base.py
"""Abstract repository contract for the Staging Engine.

Defines ``BaseStagingRepository`` — the interface that any storage backend
(in-memory, PostgreSQL, Redis, etc.) must implement to participate as a
staging store.  All methods enforce Multi-Tenant isolation via ``tenant_id``.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import StagingRecord, StagingStatus


class BaseStagingRepository(ABC):
    """Repository interface for staging record persistence.

    Every concrete implementation must guarantee that records belonging
    to different tenants are never mixed.
    """

    @abstractmethod
    def save_batch(
        self, tenant_id: str, run_id: str, records: List[StagingRecord]
    ) -> None:
        """Persist a batch of staging records atomically.

        Args:
            tenant_id: Owner tenant identifier.
            run_id: Pipeline run that produced these records.
            records: List of ``StagingRecord`` instances to store.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_by_run(
        self,
        tenant_id: str,
        run_id: str,
        status: Optional[StagingStatus] = None,
    ) -> List[StagingRecord]:
        """Retrieve records for a given run, optionally filtered by status.

        Args:
            tenant_id: Owner tenant identifier.
            run_id: Pipeline run identifier.
            status: If provided, only records with this status are returned.

        Returns:
            List of matching ``StagingRecord`` instances.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def count(
        self,
        tenant_id: str,
        run_id: str,
        status: Optional[StagingStatus] = None,
    ) -> int:
        """Count records for a run, optionally filtered by status.

        Args:
            tenant_id: Owner tenant identifier.
            run_id: Pipeline run identifier.
            status: If provided, only records with this status are counted.

        Returns:
            Integer count.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def clear(self, tenant_id: str, run_id: str) -> None:
        """Remove all records for a specific run.

        Args:
            tenant_id: Owner tenant identifier.
            run_id: Pipeline run to purge.
        """
        raise NotImplementedError  # pragma: no cover


__all__ = ["BaseStagingRepository"]
