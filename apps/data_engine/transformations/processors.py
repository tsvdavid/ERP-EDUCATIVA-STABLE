# apps/data_engine/transformations/processors.py
"""Standard declarative processors mutating and normalizing data records."""

import datetime
from decimal import Decimal
import re
from typing import Any, Callable, Dict, List, Optional, Union

from .base import BaseTransformation
from .contracts import TransformationContext
from .exceptions import ProcessorException
from .models import TransformationError
from .registry import TransformationRegistry


class RenameFieldsProcessor(BaseTransformation):
    """Renames specific dictionary keys according to a target mapping."""

    def __init__(self, mapping: Dict[str, str], context: Optional[TransformationContext] = None) -> None:
        super().__init__(context)
        self.mapping = mapping

    @property
    def name(self) -> str:
        return "rename_fields"

    @property
    def description(self) -> str:
        return f"Renames record keys using mapping: {self.mapping}"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return any(old_key in record for old_key in self.mapping)

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(record)
        for old_key, new_key in self.mapping.items():
            if old_key in out:
                out[new_key] = out.pop(old_key)
        return out

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        return []


class RemoveFieldsProcessor(BaseTransformation):
    """Removes unwanted or sensitive keys from data records."""

    def __init__(self, fields: List[str], context: Optional[TransformationContext] = None) -> None:
        super().__init__(context)
        self.fields = fields

    @property
    def name(self) -> str:
        return "remove_fields"

    @property
    def description(self) -> str:
        return f"Removes specified fields from records: {self.fields}"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return any(f in record for f in self.fields)

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(record)
        for f in self.fields:
            out.pop(f, None)
        return out

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        return []


class TypeCastProcessor(BaseTransformation):
    """Converts fields to explicit types: int, float, Decimal, bool, date, datetime."""

    def __init__(self, type_mapping: Dict[str, str], context: Optional[TransformationContext] = None) -> None:
        super().__init__(context)
        self.type_mapping = type_mapping

    @property
    def name(self) -> str:
        return "type_cast"

    @property
    def description(self) -> str:
        return f"Casts fields to target data types: {self.type_mapping}"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return any(k in record and record[k] is not None for k in self.type_mapping)

    def _cast_val(self, val: Any, target_type: str) -> Any:
        if val is None or val == "":
            return None
        target = target_type.lower().strip()
        try:
            if target == "int":
                return int(float(val)) if isinstance(val, str) and "." in val else int(val)
            if target == "float":
                return float(val)
            if target == "decimal":
                return Decimal(str(val))
            if target == "bool":
                if isinstance(val, bool):
                    return val
                s = str(val).lower().strip()
                if s in ("true", "1", "yes", "t", "y"):
                    return True
                if s in ("false", "0", "no", "f", "n"):
                    return False
                return bool(val)
            if target == "date":
                if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime):
                    return val
                if isinstance(val, datetime.datetime):
                    return val.date()
                return datetime.date.fromisoformat(str(val).split("T")[0])
            if target == "datetime":
                if isinstance(val, datetime.datetime):
                    return val
                if isinstance(val, datetime.date):
                    return datetime.datetime.combine(val, datetime.time.min)
                return datetime.datetime.fromisoformat(str(val))
            raise ProcessorException(f"Unsupported target type for cast: '{target_type}'")
        except Exception as exc:
            if isinstance(exc, ProcessorException):
                raise
            raise ProcessorException(f"Failed casting value '{val}' to '{target_type}': {exc}") from exc

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(record)
        for field_name, target_type in self.type_mapping.items():
            if field_name in out and out[field_name] is not None:
                out[field_name] = self._cast_val(out[field_name], target_type)
        return out

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        errors: List[TransformationError] = []
        for field_name, target_type in self.type_mapping.items():
            if field_name in record and record[field_name] is not None:
                try:
                    self._cast_val(record[field_name], target_type)
                except ProcessorException as exc:
                    errors.append(
                        TransformationError(
                            error_code="TYPE_CAST_ERROR",
                            error_message=str(exc),
                            transformation_name=self.name,
                            field_name=field_name,
                            original_value=record[field_name],
                        )
                    )
        return errors


class DefaultValueProcessor(BaseTransformation):
    """Populates missing or None fields with configured fallback values."""

    def __init__(self, defaults: Dict[str, Any], context: Optional[TransformationContext] = None) -> None:
        super().__init__(context)
        self.defaults = defaults

    @property
    def name(self) -> str:
        return "default_value"

    @property
    def description(self) -> str:
        return f"Injects default fallback values for missing fields: {list(self.defaults.keys())}"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return any(k not in record or record[k] is None or record[k] == "" for k in self.defaults)

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(record)
        for k, default_val in self.defaults.items():
            if k not in out or out[k] is None or out[k] == "":
                out[k] = default_val
        return out

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        return []


class TrimProcessor(BaseTransformation):
    """Strips leading and trailing whitespace from string fields."""

    def __init__(self, fields: Optional[List[str]] = None, context: Optional[TransformationContext] = None) -> None:
        super().__init__(context)
        self.fields = fields

    @property
    def name(self) -> str:
        return "trim"

    @property
    def description(self) -> str:
        return f"Trims whitespace from fields: {self.fields or 'ALL_STRINGS'}"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        target_keys = self.fields if self.fields is not None else list(record.keys())
        return any(k in record and isinstance(record[k], str) for k in target_keys)

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(record)
        target_keys = self.fields if self.fields is not None else list(record.keys())
        for k in target_keys:
            if k in out and isinstance(out[k], str):
                out[k] = out[k].strip()
        return out

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        return []


class UpperCaseProcessor(BaseTransformation):
    """Converts string fields to uppercase."""

    def __init__(self, fields: Optional[List[str]] = None, context: Optional[TransformationContext] = None) -> None:
        super().__init__(context)
        self.fields = fields

    @property
    def name(self) -> str:
        return "uppercase"

    @property
    def description(self) -> str:
        return f"Converts fields to uppercase: {self.fields or 'ALL_STRINGS'}"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        target_keys = self.fields if self.fields is not None else list(record.keys())
        return any(k in record and isinstance(record[k], str) for k in target_keys)

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(record)
        target_keys = self.fields if self.fields is not None else list(record.keys())
        for k in target_keys:
            if k in out and isinstance(out[k], str):
                out[k] = out[k].upper()
        return out

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        return []


class LowerCaseProcessor(BaseTransformation):
    """Converts string fields to lowercase."""

    def __init__(self, fields: Optional[List[str]] = None, context: Optional[TransformationContext] = None) -> None:
        super().__init__(context)
        self.fields = fields

    @property
    def name(self) -> str:
        return "lowercase"

    @property
    def description(self) -> str:
        return f"Converts fields to lowercase: {self.fields or 'ALL_STRINGS'}"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        target_keys = self.fields if self.fields is not None else list(record.keys())
        return any(k in record and isinstance(record[k], str) for k in target_keys)

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(record)
        target_keys = self.fields if self.fields is not None else list(record.keys())
        for k in target_keys:
            if k in out and isinstance(out[k], str):
                out[k] = out[k].lower()
        return out

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        return []


class RegexProcessor(BaseTransformation):
    """Performs regular expression substitution on a specific string field."""

    def __init__(
        self,
        field: str,
        pattern: str,
        replacement: str,
        context: Optional[TransformationContext] = None,
    ) -> None:
        super().__init__(context)
        self.field = field
        self.pattern = pattern
        self.replacement = replacement

    @property
    def name(self) -> str:
        return "regex_replace"

    @property
    def description(self) -> str:
        return f"Replaces regex '{self.pattern}' on field '{self.field}' with '{self.replacement}'"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return self.field in record and isinstance(record[self.field], str)

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(record)
        if self.field in out and isinstance(out[self.field], str):
            out[self.field] = re.sub(self.pattern, self.replacement, out[self.field])
        return out

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        return []


class LookupProcessor(BaseTransformation):
    """Maps values using an in-memory dictionary or callable lookup without ORM."""

    def __init__(
        self,
        field: str,
        lookup_map_or_callable: Union[Dict[Any, Any], Callable[[Any], Any]],
        target_field: Optional[str] = None,
        default: Any = None,
        context: Optional[TransformationContext] = None,
    ) -> None:
        super().__init__(context)
        self.field = field
        self.lookup_source = lookup_map_or_callable
        self.target_field = target_field or field
        self.default = default

    @property
    def name(self) -> str:
        return "lookup"

    @property
    def description(self) -> str:
        return f"Performs value lookup on '{self.field}' -> target '{self.target_field}'"

    def can_transform(self, record: Dict[str, Any]) -> bool:
        return self.field in record

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(record)
        if self.field in out:
            val = out[self.field]
            if callable(self.lookup_source):
                try:
                    res = self.lookup_source(val)
                    out[self.target_field] = res if res is not None else self.default
                except Exception:
                    out[self.target_field] = self.default
            elif isinstance(self.lookup_source, dict):
                out[self.target_field] = self.lookup_source.get(val, self.default)
            else:
                out[self.target_field] = self.default
        return out

    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        return []


# Auto-register standard processors in global registry
TransformationRegistry.global_registry().register("rename_fields", RenameFieldsProcessor)
TransformationRegistry.global_registry().register("remove_fields", RemoveFieldsProcessor)
TransformationRegistry.global_registry().register("type_cast", TypeCastProcessor)
TransformationRegistry.global_registry().register("default_value", DefaultValueProcessor)
TransformationRegistry.global_registry().register("trim", TrimProcessor)
TransformationRegistry.global_registry().register("uppercase", UpperCaseProcessor)
TransformationRegistry.global_registry().register("lowercase", LowerCaseProcessor)
TransformationRegistry.global_registry().register("regex_replace", RegexProcessor)
TransformationRegistry.global_registry().register("lookup", LookupProcessor)
