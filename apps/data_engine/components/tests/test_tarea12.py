# apps/data_engine/components/tests/test_tarea12.py
"""Unit tests for TAREA 12 — Staging Engine & Data Persistence Boundary.

Covers:
- StagingStatus enum completeness.
- StagingRecord creation, defaults, and UUID auto-generation.
- MemoryStagingRepository CRUD operations with tenant isolation.
- StagingComponent pipeline integration and audit generation.
"""

import pytest

from apps.data_engine.components.staging.models import StagingRecord, StagingStatus
from apps.data_engine.components.staging.base import BaseStagingRepository
from apps.data_engine.components.staging.repository import MemoryStagingRepository
from apps.data_engine.components.staging.component import StagingComponent
from apps.data_engine.components.base import MacContext


# ─── StagingStatus ───────────────────────────────────────────────────


def test_staging_status_values():
    """All expected lifecycle states must be present."""
    expected = {
        "RECEIVED", "PROCESSING", "VALIDATED", "REJECTED",
        "READY_IMPORT", "IMPORTED", "FAILED",
    }
    actual = {s.value for s in StagingStatus}
    assert actual == expected


def test_staging_status_is_string():
    """StagingStatus values can be compared as plain strings."""
    assert StagingStatus.VALIDATED == "VALIDATED"
    assert StagingStatus.REJECTED == "REJECTED"


# ─── StagingRecord ───────────────────────────────────────────────────


def test_staging_record_defaults():
    """A new StagingRecord should have default status RECEIVED and auto-UUID."""
    record = StagingRecord(
        tenant_id="t1", run_id="r1", row_index=0, payload={"a": 1}
    )
    assert record.status == StagingStatus.RECEIVED
    assert record.errors == []
    assert len(record.record_id) == 36  # UUID4 string


def test_staging_record_unique_ids():
    """Each StagingRecord must get a unique record_id."""
    r1 = StagingRecord(tenant_id="t1", run_id="r1", row_index=0, payload={})
    r2 = StagingRecord(tenant_id="t1", run_id="r1", row_index=1, payload={})
    assert r1.record_id != r2.record_id


def test_staging_record_with_errors():
    """A record can carry error details."""
    errors = [{"row": 0, "field": "age", "error": "out of range"}]
    record = StagingRecord(
        tenant_id="t1",
        run_id="r1",
        row_index=0,
        payload={"age": -1},
        status=StagingStatus.REJECTED,
        errors=errors,
    )
    assert record.status == StagingStatus.REJECTED
    assert len(record.errors) == 1
    assert record.errors[0]["field"] == "age"


# ─── BaseStagingRepository (abstract) ────────────────────────────────


def test_base_repository_cannot_be_instantiated():
    """BaseStagingRepository is abstract and must not be instantiated."""
    with pytest.raises(TypeError):
        BaseStagingRepository()


# ─── MemoryStagingRepository ─────────────────────────────────────────


def test_memory_repo_save_and_retrieve():
    """save_batch stores records retrievable by get_by_run."""
    repo = MemoryStagingRepository()
    records = [
        StagingRecord(
            tenant_id="t1", run_id="r1", row_index=0,
            payload={"x": 1}, status=StagingStatus.VALIDATED,
        ),
        StagingRecord(
            tenant_id="t1", run_id="r1", row_index=1,
            payload={"x": 2}, status=StagingStatus.REJECTED,
            errors=[{"row": 1, "field": "x", "error": "bad"}],
        ),
    ]
    repo.save_batch("t1", "r1", records)

    all_records = repo.get_by_run("t1", "r1")
    assert len(all_records) == 2


def test_memory_repo_filter_by_status():
    """get_by_run with status filter returns only matching records."""
    repo = MemoryStagingRepository()
    repo.save_batch("t1", "r1", [
        StagingRecord(tenant_id="t1", run_id="r1", row_index=0,
                      payload={}, status=StagingStatus.VALIDATED),
        StagingRecord(tenant_id="t1", run_id="r1", row_index=1,
                      payload={}, status=StagingStatus.REJECTED),
        StagingRecord(tenant_id="t1", run_id="r1", row_index=2,
                      payload={}, status=StagingStatus.VALIDATED),
    ])

    validated = repo.get_by_run("t1", "r1", status=StagingStatus.VALIDATED)
    rejected = repo.get_by_run("t1", "r1", status=StagingStatus.REJECTED)
    assert len(validated) == 2
    assert len(rejected) == 1


def test_memory_repo_count():
    """count returns correct totals, with and without status filter."""
    repo = MemoryStagingRepository()
    repo.save_batch("t1", "r1", [
        StagingRecord(tenant_id="t1", run_id="r1", row_index=0,
                      payload={}, status=StagingStatus.VALIDATED),
        StagingRecord(tenant_id="t1", run_id="r1", row_index=1,
                      payload={}, status=StagingStatus.REJECTED),
    ])

    assert repo.count("t1", "r1") == 2
    assert repo.count("t1", "r1", status=StagingStatus.VALIDATED) == 1
    assert repo.count("t1", "r1", status=StagingStatus.REJECTED) == 1


def test_memory_repo_clear():
    """clear removes all records for a specific run."""
    repo = MemoryStagingRepository()
    repo.save_batch("t1", "r1", [
        StagingRecord(tenant_id="t1", run_id="r1", row_index=0, payload={}),
    ])
    assert repo.count("t1", "r1") == 1

    repo.clear("t1", "r1")
    assert repo.count("t1", "r1") == 0


def test_memory_repo_tenant_isolation():
    """Records from different tenants are strictly isolated."""
    repo = MemoryStagingRepository()
    repo.save_batch("tenant_A", "r1", [
        StagingRecord(tenant_id="tenant_A", run_id="r1", row_index=0, payload={"a": 1}),
    ])
    repo.save_batch("tenant_B", "r1", [
        StagingRecord(tenant_id="tenant_B", run_id="r1", row_index=0, payload={"b": 2}),
        StagingRecord(tenant_id="tenant_B", run_id="r1", row_index=1, payload={"b": 3}),
    ])

    assert repo.count("tenant_A", "r1") == 1
    assert repo.count("tenant_B", "r1") == 2
    # Tenant A cannot see Tenant B's records
    records_a = repo.get_by_run("tenant_A", "r1")
    assert all(r.payload.get("a") for r in records_a)


def test_memory_repo_empty_queries():
    """Querying non-existent tenant/run returns empty results, not errors."""
    repo = MemoryStagingRepository()
    assert repo.get_by_run("nonexistent", "r1") == []
    assert repo.count("nonexistent", "r1") == 0


# ─── StagingComponent (Pipeline Integration) ─────────────────────────


def test_staging_component_all_valid():
    """With no validation errors, all rows should be VALIDATED."""
    comp = StagingComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "r1",
        "payload": [{"name": "Alice"}, {"name": "Bob"}],
        "metadata": {},
    }

    result = comp.execute(ctx)
    audit = result["metadata"]["staging_audit"]

    assert audit["total_records"] == 2
    assert audit["validated_count"] == 2
    assert audit["rejected_count"] == 0


def test_staging_component_with_errors():
    """Rows matching validation_errors should be REJECTED."""
    comp = StagingComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "r1",
        "payload": [
            {"name": "Alice", "age": 25},   # row 0: valid
            {"name": "Bob", "age": -5},      # row 1: invalid
            {"name": "Charlie", "age": 30},  # row 2: valid
        ],
        "metadata": {
            "validation_errors": [
                {"row": 1, "field": "age", "error": "Value below minimum"},
            ]
        },
    }

    result = comp.execute(ctx)
    audit = result["metadata"]["staging_audit"]

    assert audit["total_records"] == 3
    assert audit["validated_count"] == 2
    assert audit["rejected_count"] == 1

    # Verify individual record states
    records = result["metadata"]["staging_records"]
    assert records[0].status == StagingStatus.VALIDATED
    assert records[1].status == StagingStatus.REJECTED
    assert records[2].status == StagingStatus.VALIDATED
    # Rejected record carries its errors
    assert len(records[1].errors) == 1


def test_staging_component_multiple_errors_per_row():
    """Multiple errors on the same row still produce a single REJECTED record."""
    comp = StagingComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "r1",
        "payload": [{"name": "", "age": -1}],
        "metadata": {
            "validation_errors": [
                {"row": 0, "field": "name", "error": "required"},
                {"row": 0, "field": "age", "error": "out of range"},
            ]
        },
    }

    result = comp.execute(ctx)
    audit = result["metadata"]["staging_audit"]

    assert audit["total_records"] == 1
    assert audit["rejected_count"] == 1
    assert audit["validated_count"] == 0
    assert len(result["metadata"]["staging_records"][0].errors) == 2


def test_staging_component_empty_payload():
    """Empty payload produces zero records with clean audit."""
    comp = StagingComponent()
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "r1",
        "payload": [],
        "metadata": {},
    }

    result = comp.execute(ctx)
    audit = result["metadata"]["staging_audit"]

    assert audit["total_records"] == 0
    assert audit["validated_count"] == 0
    assert audit["rejected_count"] == 0


def test_staging_component_default_context_values():
    """Missing tenant_id/run_id should fallback to defaults, not crash."""
    comp = StagingComponent()
    ctx: MacContext = {
        "payload": [{"x": 1}],
        "metadata": {},
    }

    result = comp.execute(ctx)
    records = result["metadata"]["staging_records"]
    assert records[0].tenant_id == "default"
    assert records[0].run_id == "unknown"


def test_staging_component_with_injected_repository():
    """StagingComponent works with an externally injected repository."""
    repo = MemoryStagingRepository()
    comp = StagingComponent(repository=repo)
    ctx: MacContext = {
        "tenant_id": "t1",
        "run_id": "r1",
        "payload": [{"a": 1}, {"a": 2}],
        "metadata": {},
    }

    comp.execute(ctx)

    # The injected repo should contain the persisted records
    assert repo.count("t1", "r1") == 2
    assert repo.count("t1", "r1", status=StagingStatus.VALIDATED) == 2
