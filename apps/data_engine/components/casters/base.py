# apps/data_engine/components/casters/base.py
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Tuple

class BaseCaster(ABC):
    """Abstract base class for all casters.

    Casters convert string values to actual data types based on a schema configuration.
    They return the casted data along with any casting errors encountered.
    """

    @abstractmethod
    def cast(self, data: List[Dict[str, Any]], schema: Dict[str, str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Cast the input data values to the specified types.
        
        Args:
            data: The mapped data (List of dictionaries).
            schema: A dictionary mapping field names to data types.
                    e.g., {"age": "int", "enrollment_date": "date"}
        
        Returns:
            A tuple containing:
                - The casted data.
                - A list of error dictionaries for any casting failures.
        """
        raise NotImplementedError

__all__ = ["BaseCaster"]
