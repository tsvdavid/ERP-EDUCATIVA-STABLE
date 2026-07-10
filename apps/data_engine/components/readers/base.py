# apps/data_engine/components/readers/base.py
"""BaseReader – contract for reader implementations.

Readers are responsible for turning an arbitrary *source* (e.g. a CSV string,
file‑like object, etc.) into a raw Python data structure (typically a list of
row dictionaries).  They are deliberately stateless and must not depend on any
Django models or external services.

The MAC pipeline works with :class:`MacContext`; a reader receives the source
through its ``read`` method and returns the raw data which the orchestrator will
store in ``context["payload"]``.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseReader(ABC):
    """Abstract base class for all readers.

    Sub‑classes must implement :meth:`read` returning a ``List[Dict[str, Any]]``.
    """

    @abstractmethod
    def read(self, source: Any) -> List[Dict[str, Any]]:
        """Read *source* and return a list of row dictionaries.

        Args:
            source: The raw input – could be a string, ``Path`` object, or any
                file‑like object that the concrete implementation knows how to
                handle.
        """
        raise NotImplementedError

__all__ = ["BaseReader"]
