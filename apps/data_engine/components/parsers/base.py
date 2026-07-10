# apps/data_engine/components/parsers/base.py
from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseParser(ABC):
    """Abstract base class for all parsers.

    Parsers are responsible for interpreting the raw data structures 
    produced by Readers (e.g., converting strings to numbers, stripping whitespace).
    """

    @abstractmethod
    def parse(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse the raw data and return the interpreted data."""
        raise NotImplementedError

__all__ = ["BaseParser"]
