# apps/data_engine/integration/adapters.py
"""Simulated persistence adapters for testing and decoupled architecture."""

import copy
from typing import Any, Dict, List, Optional
from .contracts import BasePersistenceAdapter, BaseEntityMapper
from .dto import BatchPersistenceResult, PersistenceResult, RejectedRecord
from .exceptions import PersistenceError
from .mappers import StudentMapper, TeacherMapper, RepresentativeMapper, FinancialMapper


class SimulatedStorage:
    """In-memory mock database to simulate transactional commit and rollback."""

    def __init__(self) -> None:
        self.tables: Dict[str, List[Dict[str, Any]]] = {}
        self.backup: Optional[Dict[str, List[Dict[str, Any]]]] = None

    def create_backup(self) -> None:
        """Create a deep copy backup of current state."""
        self.backup = copy.deepcopy(self.tables)

    def restore_backup(self) -> None:
        """Restore database state from the backup."""
        if self.backup is not None:
            self.tables = self.backup

    def clear(self) -> None:
        """Clear all database tables."""
        self.tables.clear()
        self.backup = None


# Central database instance for simulation
simulated_db = SimulatedStorage()


class SimulatedAdapter(BasePersistenceAdapter):
    """Generic in-memory persistence adapter executing maps and simulated writes."""

    def __init__(self, table_name: str, mapper: BaseEntityMapper) -> None:
        self.table_name = table_name
        self.mapper = mapper

    def _get_table(self) -> List[Dict[str, Any]]:
        return simulated_db.tables.setdefault(self.table_name, [])

    def persist(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> PersistenceResult:
        try:
            mapped_data = self.mapper.map_record(record, context)
            ident = mapped_data.get("identification") or mapped_data.get("fee_code")
            if not ident:
                return PersistenceResult(
                    success=False,
                    error_message="Missing primary key identifier in mapped record",
                    original_data=record
                )

            table = self._get_table()
            existing = None
            for row in table:
                if row.get("identification") == ident or row.get("fee_code") == ident:
                    existing = row
                    break

            if existing is not None:
                # Update record
                existing.update(mapped_data)
                return PersistenceResult(success=True, record_id=ident, created=False, original_data=record)
            else:
                # Insert record
                table.append(mapped_data)
                return PersistenceResult(success=True, record_id=ident, created=True, original_data=record)
        except Exception as e:
            return PersistenceResult(success=False, error_message=str(e), original_data=record)

    def persist_batch(self, records: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> BatchPersistenceResult:
        results = []
        rejected = []
        success_count = 0
        failed_count = 0

        # Create rollback point
        simulated_db.create_backup()

        try:
            for rec in records:
                res = self.persist(rec, context)
                results.append(res)
                if res.success:
                    success_count += 1
                else:
                    failed_count += 1
                    rejected.append(RejectedRecord(record=rec, reason=res.error_message or "Unknown failure"))

            if failed_count > 0:
                # Rollback transaction on batch failure
                simulated_db.restore_backup()
                return BatchPersistenceResult(
                    processed_count=len(records),
                    success_count=0,
                    failed_count=len(records),
                    results=results,
                    rejected_records=[
                        RejectedRecord(record=r.record, reason="Transaction rolled back due to batch errors")
                        for r in rejected
                    ]
                )

            return BatchPersistenceResult(
                processed_count=len(records),
                success_count=success_count,
                failed_count=0,
                results=results,
                rejected_records=[]
            )
        except Exception as e:
            simulated_db.restore_backup()
            raise PersistenceError(f"Batch persistence failed: {e}") from e


class StudentAdapter(SimulatedAdapter):
    """Adapter for student persistence."""

    def __init__(self) -> None:
        super().__init__("student", StudentMapper())


class TeacherAdapter(SimulatedAdapter):
    """Adapter for teacher persistence."""

    def __init__(self) -> None:
        super().__init__("teacher", TeacherMapper())


class RepresentativeAdapter(SimulatedAdapter):
    """Adapter for representative persistence."""

    def __init__(self) -> None:
        super().__init__("representative", RepresentativeMapper())


class FinancialAdapter(SimulatedAdapter):
    """Adapter for financial fee persistence."""

    def __init__(self) -> None:
        super().__init__("financial", FinancialMapper())
