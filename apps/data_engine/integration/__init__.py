# apps/data_engine/integration/__init__.py
"""ERP Integration Layer & Persistence Gateway module (TAREA 32)."""

from .contracts import (
    BaseEntityMapper,
    BaseIntegrationService,
    BasePersistenceAdapter,
    BaseTransactionManager,
)
from .dto import (
    BatchPersistenceResult,
    EntityMapping,
    PersistenceRequest,
    PersistenceResult,
    RejectedRecord,
)
from .exceptions import (
    AdapterNotFoundError,
    IntegrationException,
    MappingError,
    PersistenceError,
    TransactionError,
)
from .registry import IntegrationRegistry
from .services import MacIntegrationService
from .transaction import InMemoryTransactionManager
from .adapters import (
    StudentAdapter,
    TeacherAdapter,
    RepresentativeAdapter,
    FinancialAdapter,
    simulated_db,
)


def register_builtin_adapters() -> None:
    """Register built-in entity persistence adapters on startup."""
    registry = IntegrationRegistry.global_registry()
    registry.register("student", StudentAdapter())
    registry.register("teacher", TeacherAdapter())
    registry.register("representative", RepresentativeAdapter())
    registry.register("financial", FinancialAdapter())


# Automatically register on package load
register_builtin_adapters()

__all__ = [
    "BaseEntityMapper",
    "BasePersistenceAdapter",
    "BaseTransactionManager",
    "BaseIntegrationService",
    "EntityMapping",
    "PersistenceRequest",
    "PersistenceResult",
    "RejectedRecord",
    "BatchPersistenceResult",
    "IntegrationException",
    "MappingError",
    "PersistenceError",
    "TransactionError",
    "AdapterNotFoundError",
    "IntegrationRegistry",
    "MacIntegrationService",
    "InMemoryTransactionManager",
    "StudentAdapter",
    "TeacherAdapter",
    "RepresentativeAdapter",
    "FinancialAdapter",
    "simulated_db",
    "register_builtin_adapters",
]
