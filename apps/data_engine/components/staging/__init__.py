# apps/data_engine/components/staging/__init__.py
"""Staging package for MAC.

Contains the Staging Engine boundary, separating in-memory processing
from persistent storage through the Repository pattern.
"""

from .models import StagingRecord, StagingStatus
from .base import BaseStagingRepository
from .repository import MemoryStagingRepository
from .component import StagingComponent

__all__ = [
    "StagingRecord",
    "StagingStatus",
    "BaseStagingRepository",
    "MemoryStagingRepository",
    "StagingComponent"
]
