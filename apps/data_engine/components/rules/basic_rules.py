import re
from typing import Any, Optional, Type

from .base import BaseRule

class RequiredRule(BaseRule):
    """Fails if the value is None or an empty string."""
    def validate(self, field_name: str, value: Any) -> Optional[str]:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return f"Field '{field_name}' is required."
        return None

class TypeRule(BaseRule):
    """Fails if the value is not of the specified type."""
    def __init__(self, expected_type: Type):
        self.expected_type = expected_type
        
    def validate(self, field_name: str, value: Any) -> Optional[str]:
        if value is not None and not isinstance(value, self.expected_type):
            return f"Field '{field_name}' must be of type {self.expected_type.__name__}."
        return None

class LengthRule(BaseRule):
    """Fails if the string length is outside the specified bounds."""
    def __init__(self, min_length: int = None, max_length: int = None):
        self.min_length = min_length
        self.max_length = max_length
        
    def validate(self, field_name: str, value: Any) -> Optional[str]:
        if value is None:
            return None
            
        if not isinstance(value, str):
            return f"Field '{field_name}' must be a string to check length."
            
        length = len(value)
        if self.min_length is not None and length < self.min_length:
            return f"Field '{field_name}' must be at least {self.min_length} characters long."
        if self.max_length is not None and length > self.max_length:
            return f"Field '{field_name}' must be at most {self.max_length} characters long."
            
        return None

class RangeRule(BaseRule):
    """Fails if a numeric value is outside the specified bounds."""
    def __init__(self, min_value: float = None, max_value: float = None):
        self.min_value = min_value
        self.max_value = max_value
        
    def validate(self, field_name: str, value: Any) -> Optional[str]:
        if value is None:
            return None
            
        if not isinstance(value, (int, float)):
            return f"Field '{field_name}' must be a number to check range."
            
        if self.min_value is not None and value < self.min_value:
            return f"Field '{field_name}' must be >= {self.min_value}."
        if self.max_value is not None and value > self.max_value:
            return f"Field '{field_name}' must be <= {self.max_value}."
            
        return None

class PatternRule(BaseRule):
    """Fails if the string value does not match the regex pattern."""
    def __init__(self, pattern: str):
        try:
            self.regex = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{pattern}': {e}")
            
    def validate(self, field_name: str, value: Any) -> Optional[str]:
        if value is None:
            return None
            
        if not isinstance(value, str):
            return f"Field '{field_name}' must be a string to check pattern."
            
        if not self.regex.match(value):
            return f"Field '{field_name}' does not match the required pattern."
            
        return None
