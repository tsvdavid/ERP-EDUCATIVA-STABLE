# apps/data_engine/transformations/validators.py
"""Standalone declarative validators enforcing business rules during pipeline execution."""

import re
from typing import Any, Callable, Dict, List, Optional, Set

from .base import BaseTransformation
from .contracts import TransformationContext
from .models import TransformationError
from .registry import TransformationRegistry


class RequiredValidator(BaseTransformation):
    """Checks that mandatory fields are present and not None/empty."""

    def __init__(self, fields: List[str], context: Optional[TransformationContext] = None) -> None:
        super().__init__(context)
        self.fields = fields

    @property
    def name(self) -> str:
        return "required_validator"

    @property
    def description(self) -> str:
        return f"Enforces that fields {self.fields} are present and non-empty."

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return True

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return dict(record)

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        errors: List[TransformationError] = []
        for f in self.fields:
            if f not in record or record[f] is None or (isinstance(record[f], str) and record[f].strip() == ""):
                errors.append(
                    TransformationError(
                        error_code="REQUIRED_FIELD_MISSING",
                        error_message=f"Mandatory field '{f}' is missing or empty.",
                        transformation_name=self.name,
                        field_name=f,
                        original_value=record.get(f),
                    )
                )
        return errors


class RegexValidator(BaseTransformation):
    """Validates string fields against a regular expression pattern."""

    def __init__(
        self,
        field: str,
        pattern: str,
        message: Optional[str] = None,
        context: Optional[TransformationContext] = None,
    ) -> None:
        super().__init__(context)
        self.field = field
        self.pattern = pattern
        self.message = message or f"Field '{field}' does not match pattern '{pattern}'."
        self._compiled = re.compile(pattern)

    @property
    def name(self) -> str:
        return "regex_validator"

    @property
    def description(self) -> str:
        return f"Validates that field '{self.field}' matches regular expression '{self.pattern}'."

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return self.field in record and record[self.field] is not None

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return dict(record)

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        val = record.get(self.field)
        if val is None:
            return []
        if not isinstance(val, str) or not self._compiled.match(val):
            return [
                TransformationError(
                    error_code="REGEX_MISMATCH",
                    error_message=self.message,
                    transformation_name=self.name,
                    field_name=self.field,
                    original_value=val,
                )
            ]
        return []


class RangeValidator(BaseTransformation):
    """Validates that a numeric or comparable field falls within a specified boundaries (`min_val`, `max_val`)."""

    def __init__(
        self,
        field: str,
        min_val: Optional[Any] = None,
        max_val: Optional[Any] = None,
        context: Optional[TransformationContext] = None,
    ) -> None:
        super().__init__(context)
        self.field = field
        self.min_val = min_val
        self.max_val = max_val

    @property
    def name(self) -> str:
        return "range_validator"

    @property
    def description(self) -> str:
        return f"Validates range of field '{self.field}': [{self.min_val}, {self.max_val}]"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return self.field in record and record[self.field] is not None

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return dict(record)

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        val = record.get(self.field)
        if val is None:
            return []
        try:
            v_comp = val
            min_comp = self.min_val
            max_comp = self.max_val
            if isinstance(val, str) and (isinstance(self.min_val, (int, float)) or isinstance(self.max_val, (int, float)) or hasattr(self.min_val, "as_tuple") or hasattr(self.max_val, "as_tuple")):
                try:
                    v_comp = float(val)
                    if self.min_val is not None:
                        min_comp = float(self.min_val)
                    if self.max_val is not None:
                        max_comp = float(self.max_val)
                except ValueError:
                    pass

            if min_comp is not None and v_comp < min_comp:
                return [
                    TransformationError(
                        error_code="RANGE_BELOW_MINIMUM",
                        error_message=f"Value {val} is below minimum {self.min_val}.",
                        transformation_name=self.name,
                        field_name=self.field,
                        original_value=val,
                    )
                ]
            if max_comp is not None and v_comp > max_comp:
                return [
                    TransformationError(
                        error_code="RANGE_ABOVE_MAXIMUM",
                        error_message=f"Value {val} is above maximum {self.max_val}.",
                        transformation_name=self.name,
                        field_name=self.field,
                        original_value=val,
                    )
                ]
        except TypeError as exc:
            return [
                TransformationError(
                    error_code="RANGE_COMPARISON_ERROR",
                    error_message=f"Cannot compare value {val} of type {type(val).__name__}: {exc}",
                    transformation_name=self.name,
                    field_name=self.field,
                    original_value=val,
                )
            ]
        return []


class UniqueValidator(BaseTransformation):
    """Tracks values seen across records in memory and flags duplicate occurrences within the run."""

    def __init__(self, field: str, context: Optional[TransformationContext] = None) -> None:
        super().__init__(context)
        self.field = field
        self._seen: Set[Any] = set()

    @property
    def name(self) -> str:
        return "unique_validator"

    @property
    def description(self) -> str:
        return f"Enforces in-memory uniqueness on field '{self.field}' during pipeline execution."

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return self.field in record

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return dict(record)

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        val = record.get(self.field)
        if val is None:
            return []
        if val in self._seen:
            return [
                TransformationError(
                    error_code="DUPLICATE_VALUE",
                    error_message=f"Duplicate value encountered for field '{self.field}': '{val}'.",
                    transformation_name=self.name,
                    field_name=self.field,
                    original_value=val,
                )
            ]
        self._seen.add(val)
        return []

    def reset(self) -> None:
        """Clear internal tracking set."""
        self._seen.clear()


class LengthValidator(BaseTransformation):
    """Validates length of strings, lists, or collections against minimum/maximum bounds."""

    def __init__(
        self,
        field: str,
        min_len: Optional[int] = None,
        max_len: Optional[int] = None,
        context: Optional[TransformationContext] = None,
    ) -> None:
        super().__init__(context)
        self.field = field
        self.min_len = min_len
        self.max_len = max_len

    @property
    def name(self) -> str:
        return "length_validator"

    @property
    def description(self) -> str:
        return f"Checks length of '{self.field}' is within [{self.min_len}, {self.max_len}]."

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return self.field in record and record[self.field] is not None

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return dict(record)

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        val = record.get(self.field)
        if val is None:
            return []
        try:
            length = len(val)
            if self.min_len is not None and length < self.min_len:
                return [
                    TransformationError(
                        error_code="LENGTH_BELOW_MINIMUM",
                        error_message=f"Length {length} is less than minimum {self.min_len}.",
                        transformation_name=self.name,
                        field_name=self.field,
                        original_value=val,
                    )
                ]
            if self.max_len is not None and length > self.max_len:
                return [
                    TransformationError(
                        error_code="LENGTH_ABOVE_MAXIMUM",
                        error_message=f"Length {length} exceeds maximum {self.max_len}.",
                        transformation_name=self.name,
                        field_name=self.field,
                        original_value=val,
                    )
                ]
        except TypeError:
            return [
                TransformationError(
                    error_code="LENGTH_CHECK_FAILED",
                    error_message=f"Field '{self.field}' of type {type(val).__name__} does not support length check.",
                    transformation_name=self.name,
                    field_name=self.field,
                    original_value=val,
                )
            ]
        return []


class EnumValidator(BaseTransformation):
    """Checks that a field value is contained within an explicit list of allowed choices."""

    def __init__(
        self,
        field: str,
        allowed_values: List[Any],
        context: Optional[TransformationContext] = None,
    ) -> None:
        super().__init__(context)
        self.field = field
        self.allowed_values = allowed_values

    @property
    def name(self) -> str:
        return "enum_validator"

    @property
    def description(self) -> str:
        return f"Ensures field '{self.field}' is one of: {self.allowed_values}"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return self.field in record and record[self.field] is not None

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return dict(record)

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        val = record.get(self.field)
        if val is not None and val not in self.allowed_values:
            return [
                TransformationError(
                    error_code="INVALID_ENUM_VALUE",
                    error_message=f"Value '{val}' is not in allowed choices: {self.allowed_values}.",
                    transformation_name=self.name,
                    field_name=self.field,
                    original_value=val,
                )
            ]
        return []


class CustomValidator(BaseTransformation):
    """Executes a custom lambda or callable validator function against incoming records."""

    def __init__(
        self,
        validator_func: Callable[[Dict[str, Any]], List[TransformationError]],
        name: str = "custom_validator",
        description: str = "Executes custom functional validation logic.",
        context: Optional[TransformationContext] = None,
    ) -> None:
        super().__init__(context)
        self.validator_func = validator_func
        self._name = name
        self._desc = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._desc

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return True

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return dict(record)

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        return self.validator_func(record)


# Auto-register standalone validators into global registry
TransformationRegistry.global_registry().register("required_validator", RequiredValidator)
TransformationRegistry.global_registry().register("regex_validator", RegexValidator)
TransformationRegistry.global_registry().register("range_validator", RangeValidator)
TransformationRegistry.global_registry().register("unique_validator", UniqueValidator)
TransformationRegistry.global_registry().register("length_validator", LengthValidator)
TransformationRegistry.global_registry().register("enum_validator", EnumValidator)
TransformationRegistry.global_registry().register("custom_validator", CustomValidator)
