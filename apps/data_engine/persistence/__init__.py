# apps/data_engine/persistence/__init__.py
"""Transactional Persistence Adapter & ORM Integration Framework (TAREA 18).

Bridges the pure MAC Execution Engine (Layer 11) with Django ORM while maintaining
complete architectural decoupling (`Zero-ORM outside persistence/`).

Exports:
- ``BaseRepository``, ``BasePersistenceExecutor``: Abstract contracts.
- ``EntityPersistenceResult``, ``TransactionResult``, ``PersistenceContext``: Domain entities.
- ``RepositoryRegistry``, ``RepositoryResolver``: Repository management and lookup utilities.
- ``DjangoOrmStepExecutor``: Concrete step executor implementing ``BaseStepExecutor``.
- Concrete Repositories: ``InstitutionRepository``, ``AcademicPeriodRepository``, ``CourseRepository``,
  ``StudentRepository``, ``RepresentativeRepository``, ``EnrollmentRepository``.
"""

from .adapters import RepositoryResolver
from .base import BasePersistenceExecutor, BaseRepository
from .executor import DjangoOrmStepExecutor
from .models import EntityPersistenceResult, PersistenceContext, TransactionResult
from .registry import RepositoryRegistry
from .repositories import (
    AcademicPeriodRepository,
    CourseRepository,
    EnrollmentRepository,
    InstitutionRepository,
    RepresentativeRepository,
    StudentRepository,
)


def register_builtin_repositories() -> None:
    """Register all built-in repositories with the `RepositoryRegistry`."""
    RepositoryRegistry.register(InstitutionRepository)
    RepositoryRegistry.register(AcademicPeriodRepository)
    RepositoryRegistry.register(CourseRepository)
    RepositoryRegistry.register(StudentRepository)
    RepositoryRegistry.register(RepresentativeRepository)
    RepositoryRegistry.register(EnrollmentRepository)


# Automatically register built-in repositories on module initialization
register_builtin_repositories()

__all__ = [
    "BaseRepository",
    "BasePersistenceExecutor",
    "EntityPersistenceResult",
    "TransactionResult",
    "PersistenceContext",
    "RepositoryRegistry",
    "RepositoryResolver",
    "DjangoOrmStepExecutor",
    "InstitutionRepository",
    "AcademicPeriodRepository",
    "CourseRepository",
    "StudentRepository",
    "RepresentativeRepository",
    "EnrollmentRepository",
    "register_builtin_repositories",
]
