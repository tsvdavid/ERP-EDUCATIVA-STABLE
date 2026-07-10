# apps/data_engine/components/mappers/base.py
from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseMapper(ABC):
    """Abstract base class for all mappers.

    Mappers transform the keys of the input dictionaries based on a mapping configuration.
    """

    @abstractmethod
    def map(self, data: List[Dict[str, Any]], config: Dict[str, str]) -> List[Dict[str, Any]]:
        """Map the input data keys to standardized internal keys.
        
        Args:
            data: The raw parsed data (List of dictionaries).
            config: A dictionary mapping source keys to target keys.
                    e.g., {"Cédula": "national_id"}
        
        Returns:
            The mapped data.
        """
        raise NotImplementedError

__all__ = ["BaseMapper"]
