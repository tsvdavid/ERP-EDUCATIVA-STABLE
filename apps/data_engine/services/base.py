# apps/data_engine/services/base.py
"""Base class for MAC service components.

All concrete services should inherit from ``BaseService`` and implement
the ``execute`` method, which receives a ``context`` dict.
"""

from abc import ABC, abstractmethod


class BaseService(ABC):
    """Abstract service class for MAC components."""

    @abstractmethod
    def execute(self, context: dict) -> any:
        """Execute the service logic.

        Parameters
        ----------
        context: dict
            Arbitrary data required for execution.
        """
        raise NotImplementedError
