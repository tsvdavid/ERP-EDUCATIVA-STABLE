# apps/data_engine/components/rules/base.py
from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseRule(ABC):
    """Abstract base class for all validation rules.
    
    A rule evaluates a single value and returns None if valid, 
    or an error string if invalid.
    """

    @abstractmethod
    def validate(self, field_name: str, value: Any) -> Optional[str]:
        """Evaluate the value.
        
        Args:
            field_name: The name of the field being validated (useful for error messages).
            value: The value to validate.
            
        Returns:
            None if the value passes the rule.
            An error message string if the value fails the rule.
        """
        raise NotImplementedError

__all__ = ["BaseRule"]
