# apps/data_engine/quality/rules.py
"""Implementations of built-in, reusable data quality rules."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
import threading
from typing import Any, Callable, Dict, List, Optional, Set

from apps.data_engine.quality.base import BaseQualityRule
from apps.data_engine.quality.models import QualityViolation


class RequiredRule(BaseQualityRule):
    """Rule ensuring that a targeted field is present and non-empty."""

    def __init__(self, field: str, severity: str = "ERROR") -> None:
        self._field = field
        self._severity = severity

    @property
    def code(self) -> str:
        return f"REQUIRED_{self._field.upper()}"

    @property
    def field(self) -> str:
        return self._field

    @property
    def severity(self) -> str:
        return self._severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        val = record.get(self._field)
        if val is None or (isinstance(val, str) and not val.strip()):
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=f"Field '{self._field}' is required and cannot be empty.",
                    severity=self._severity,
                    value=val,
                )
            ]
        return []


class RegexRule(BaseQualityRule):
    """Rule checking if field value conforms to a defined regular expression pattern."""

    def __init__(self, field: str, pattern: str, severity: str = "ERROR", message: str = "") -> None:
        self._field = field
        self._pattern = pattern
        self._regex = re.compile(pattern)
        self._severity = severity
        self._message = message

    @property
    def code(self) -> str:
        return f"REGEX_{self._field.upper()}"

    @property
    def field(self) -> str:
        return self._field

    @property
    def severity(self) -> str:
        return self._severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        val = record.get(self._field)
        if val is None or val == "":
            return []
        
        if not self._regex.match(str(val)):
            msg = self._message or f"Field '{self._field}' value '{val}' does not match pattern '{self._pattern}'."
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=msg,
                    severity=self._severity,
                    value=val,
                )
            ]
        return []


class RangeRule(BaseQualityRule):
    """Rule verifying that a numeric field lies within a minimum and maximum boundary."""

    def __init__(self, field: str, min_value: Any = None, max_value: Any = None, severity: str = "ERROR") -> None:
        self._field = field
        self._min = min_value
        self._max = max_value
        self._severity = severity

    @property
    def code(self) -> str:
        return f"RANGE_{self._field.upper()}"

    @property
    def field(self) -> str:
        return self._field

    @property
    def severity(self) -> str:
        return self._severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        raw_val = record.get(self._field)
        if raw_val is None or raw_val == "":
            return []

        try:
            val = float(raw_val)
        except (ValueError, TypeError):
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=f"Field '{self._field}' value '{raw_val}' is not a valid number.",
                    severity=self._severity,
                    value=raw_val,
                )
            ]

        if self._min is not None and val < float(self._min):
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=f"Field '{self._field}' value {val} is below minimum allowed value of {self._min}.",
                    severity=self._severity,
                    value=raw_val,
                )
            ]
        if self._max is not None and val > float(self._max):
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=f"Field '{self._field}' value {val} exceeds maximum allowed value of {self._max}.",
                    severity=self._severity,
                    value=raw_val,
                )
            ]
        return []


class EnumRule(BaseQualityRule):
    """Rule ensuring that a field's value belongs to a set of allowed options."""

    def __init__(self, field: str, allowed_values: List[Any], severity: str = "ERROR") -> None:
        self._field = field
        self._allowed = set(allowed_values)
        self._severity = severity

    @property
    def code(self) -> str:
        return f"ENUM_{self._field.upper()}"

    @property
    def field(self) -> str:
        return self._field

    @property
    def severity(self) -> str:
        return self._severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        val = record.get(self._field)
        if val is None or val == "":
            return []

        if val not in self._allowed:
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=f"Field '{self._field}' value '{val}' is not in allowed choices {sorted(list(self._allowed))}.",
                    severity=self._severity,
                    value=val,
                )
            ]
        return []


class UniqueRule(BaseQualityRule):
    """Rule asserting field uniqueness across all records. Thread-safe using context map locks."""

    def __init__(self, field: str, severity: str = "ERROR") -> None:
        self._field = field
        self._severity = severity

    @property
    def code(self) -> str:
        return f"UNIQUE_{self._field.upper()}"

    @property
    def field(self) -> str:
        return self._field

    @property
    def severity(self) -> str:
        return self._severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        val = record.get(self._field)
        if val is None or val == "":
            return []

        ctx = context if context is not None else {}
        
        # Resolve lock for thread-safe state checking
        lock = ctx.setdefault("_unique_lock", threading.Lock())
        seen_map = ctx.setdefault("_seen_unique_values", {})
        
        with lock:
            seen_set = seen_map.setdefault(self._field, set())
            if val in seen_set:
                return [
                    QualityViolation(
                        rule_code=self.code,
                        field=self._field,
                        message=f"Field '{self._field}' value '{val}' is duplicated.",
                        severity=self._severity,
                        value=val,
                    )
                ]
            seen_set.add(val)
            
        return []


class LengthRule(BaseQualityRule):
    """Rule defining bounds for character string lengths."""

    def __init__(self, field: str, min_length: Optional[int] = None, max_length: Optional[int] = None, severity: str = "ERROR") -> None:
        self._field = field
        self._min = min_length
        self._max = max_length
        self._severity = severity

    @property
    def code(self) -> str:
        return f"LENGTH_{self._field.upper()}"

    @property
    def field(self) -> str:
        return self._field

    @property
    def severity(self) -> str:
        return self._severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        val = record.get(self._field)
        if val is None:
            return []

        val_str = str(val)
        length = len(val_str)

        if self._min is not None and length < self._min:
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=f"Field '{self._field}' length {length} is shorter than minimum {self._min}.",
                    severity=self._severity,
                    value=val,
                )
            ]
        if self._max is not None and length > self._max:
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=f"Field '{self._field}' length {length} exceeds maximum {self._max}.",
                    severity=self._severity,
                    value=val,
                )
            ]
        return []


class EmailRule(BaseQualityRule):
    """Rule validating electronic mail address format."""

    def __init__(self, field: str, severity: str = "ERROR") -> None:
        self._field = field
        self._severity = severity
        self._regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    @property
    def code(self) -> str:
        return f"EMAIL_{self._field.upper()}"

    @property
    def field(self) -> str:
        return self._field

    @property
    def severity(self) -> str:
        return self._severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        val = record.get(self._field)
        if val is None or val == "":
            return []

        if not self._regex.match(str(val)):
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=f"Field '{self._field}' value '{val}' is not a valid email address.",
                    severity=self._severity,
                    value=val,
                )
            ]
        return []


class DateRule(BaseQualityRule):
    """Rule checking if date formats conform to semantic formats."""

    def __init__(self, field: str, format_str: str = "%Y-%m-%d", severity: str = "ERROR") -> None:
        self._field = field
        self._format = format_str
        self._severity = severity

    @property
    def code(self) -> str:
        return f"DATE_{self._field.upper()}"

    @property
    def field(self) -> str:
        return self._field

    @property
    def severity(self) -> str:
        return self._severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        val = record.get(self._field)
        if val is None or val == "":
            return []

        try:
            datetime.strptime(str(val).strip(), self._format)
        except ValueError:
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=f"Field '{self._field}' value '{val}' does not match date format '{self._format}'.",
                    severity=self._severity,
                    value=val,
                )
            ]
        return []


class NumericRule(BaseQualityRule):
    """Rule validating that a field's value represents a valid number."""

    def __init__(self, field: str, severity: str = "ERROR") -> None:
        self._field = field
        self._severity = severity

    @property
    def code(self) -> str:
        return f"NUMERIC_{self._field.upper()}"

    @property
    def field(self) -> str:
        return self._field

    @property
    def severity(self) -> str:
        return self._severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        val = record.get(self._field)
        if val is None or val == "":
            return []

        try:
            float(val)
        except (ValueError, TypeError):
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=f"Field '{self._field}' value '{val}' is not a valid number.",
                    severity=self._severity,
                    value=val,
                )
            ]
        return []


class ReferenceRule(BaseQualityRule):
    """Rule checking values against a given reference set."""

    def __init__(self, field: str, allowed_references: Set[Any], severity: str = "ERROR") -> None:
        self._field = field
        self._refs = allowed_references
        self._severity = severity

    @property
    def code(self) -> str:
        return f"REFERENCE_{self._field.upper()}"

    @property
    def field(self) -> str:
        return self._field

    @property
    def severity(self) -> str:
        return self._severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        val = record.get(self._field)
        if val is None or val == "":
            return []

        if val not in self._refs:
            return [
                QualityViolation(
                    rule_code=self.code,
                    field=self._field,
                    message=f"Field '{self._field}' reference value '{val}' is not present in references.",
                    severity=self._severity,
                    value=val,
                )
            ]
        return []


class CompositeRule(BaseQualityRule):
    """Rule composing multiple rules checked conjunctively."""

    def __init__(self, rules: List[BaseQualityRule], severity: str = "ERROR") -> None:
        self._rules = rules
        self._severity = severity

    @property
    def code(self) -> str:
        return f"COMPOSITE_{'_'.join([r.field for r in self._rules if r.field])}"

    @property
    def field(self) -> Optional[str]:
        return None

    @property
    def severity(self) -> str:
        return self._severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        violations: List[QualityViolation] = []
        for r in self._rules:
            violations.extend(r.validate(record, context))
        return violations


class ConditionalRule(BaseQualityRule):
    """Rule conditionally evaluated based on custom record checks."""

    def __init__(self, condition: Callable[[Dict[str, Any]], bool], rule: BaseQualityRule) -> None:
        self._condition = condition
        self._rule = rule

    @property
    def code(self) -> str:
        return f"CONDITIONAL_{self._rule.code}"

    @property
    def field(self) -> Optional[str]:
        return self._rule.field

    @property
    def severity(self) -> str:
        return self._rule.severity

    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        if self._condition(record):
            return self._rule.validate(record, context)
        return []
