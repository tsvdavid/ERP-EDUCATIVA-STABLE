# apps/data_engine/components/importers/base.py
"""Abstract strategy contract for the Import Engine.

Defines ``BaseImportStrategy`` — the interface that any import backend
must implement. The Strategy pattern decouples import orchestration
from the persistence mechanism:

- ``DryRunStrategy``: Simulates import (TAREA 13).
- ``DjangoStrategy``: Persists via ORM (future).
"""

from abc import ABC, abstractmethod

from .models import ImportBatch, ImportResult


class BaseImportStrategy(ABC):
    """Strategy interface for import execution.

    Implementations decide HOW to import the data contained in a batch.
    The strategy must not have knowledge of the pipeline context — it
    operates purely on ``ImportBatch`` and returns ``ImportResult``.
    """

    @abstractmethod
    def execute(self, batch: ImportBatch) -> ImportResult:
        """Process a batch and return the consolidated result.

        Args:
            batch: The ``ImportBatch`` containing items to import.

        Returns:
            An ``ImportResult`` with updated item statuses and metrics.
        """
        raise NotImplementedError  # pragma: no cover


__all__ = ["BaseImportStrategy"]
