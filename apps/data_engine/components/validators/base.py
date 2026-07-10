# apps/data_engine/components/validators/base.py
from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseValidator(ABC):
    """Abstract base class for all validators.

    Validators inspect the payload data without mutating it and return a list 
    of error dictionaries if validation fails.
    """

    @abstractmethod
    def validate(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate the data.
        
        Returns:
            A list of error dictionaries. If empty, the data is valid.
        """
        raise NotImplementedError

__all__ = ["BaseValidator"]
