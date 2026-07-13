# apps/data_engine/integration/transaction.py
"""Simulated in-memory Transaction Manager for testing and decoupled architecture."""

from typing import Any
from .contracts import BaseTransactionManager


class InMemoryTransactionManager(BaseTransactionManager):
    """Simulates multi-tenant transaction tracking and atomic rollback capabilities."""

    def __init__(self) -> None:
        self.is_active = False
        self.was_committed = False
        self.was_rolled_back = False

    def begin(self) -> None:
        self.is_active = True
        self.was_committed = False
        self.was_rolled_back = False

    def commit(self) -> None:
        if not self.is_active:
            raise ValueError("No active transaction to commit.")
        self.is_active = False
        self.was_committed = True

    def rollback(self) -> None:
        if not self.is_active:
            raise ValueError("No active transaction to rollback.")
        self.is_active = False
        self.was_rolled_back = True

    def __enter__(self) -> "InMemoryTransactionManager":
        self.begin()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            if self.is_active:
                self.commit()
