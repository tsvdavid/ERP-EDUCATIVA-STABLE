# apps/data_engine/components/staging/repository.py
"""In-memory implementation of the Staging Repository.

``MemoryStagingRepository`` is an ephemeral store intended for:
- Unit testing without external dependencies.
- Freezing the architectural contract before implementing database persistence.

Data is stored in a nested dict: ``{tenant_id: {run_id: [StagingRecord, ...]}}``.
"""

from collections import defaultdict
from typing import Dict, List, Optional

from .base import BaseStagingRepository
from .models import StagingRecord, StagingStatus


class MemoryStagingRepository(BaseStagingRepository):
    """Ephemeral in-memory staging repository.

    Records are kept in plain Python data structures and will be
    garbage-collected when the repository instance is released.
    """

    def __init__(self) -> None:
        # _store: tenant_id → run_id → list of StagingRecord
        self._store: Dict[str, Dict[str, List[StagingRecord]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def save_batch(
        self, tenant_id: str, run_id: str, records: List[StagingRecord]
    ) -> None:
        """Append records to the in-memory store."""
        self._store[tenant_id][run_id].extend(records)

    def get_by_run(
        self,
        tenant_id: str,
        run_id: str,
        status: Optional[StagingStatus] = None,
    ) -> List[StagingRecord]:
        """Return records for a run, with optional status filter."""
        records = self._store.get(tenant_id, {}).get(run_id, [])
        if status is not None:
            return [r for r in records if r.status == status]
        return list(records)

    def count(
        self,
        tenant_id: str,
        run_id: str,
        status: Optional[StagingStatus] = None,
    ) -> int:
        """Count records, with optional status filter."""
        return len(self.get_by_run(tenant_id, run_id, status))

    def clear(self, tenant_id: str, run_id: str) -> None:
        """Remove all records for a specific run."""
        if tenant_id in self._store and run_id in self._store[tenant_id]:
            del self._store[tenant_id][run_id]


__all__ = ["MemoryStagingRepository"]
