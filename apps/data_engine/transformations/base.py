# apps/data_engine/transformations/base.py
"""Abstract base contract for declarative ETL data transformations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from apps.data_engine.components.base import BaseComponent, MacContext
from .contracts import TransformationContext
from .models import TransformationError


class BaseTransformation(BaseComponent, ABC):
    """Abstract base class for all declarative data transformations and validators.

    Subclasses must define `name`, `description`, `can_transform()`, `transform()`,
    and `validate()` to convert or inspect incoming dictionary records.
    """

    component_type: str = "transformation"

    def __init__(self, context: Optional[TransformationContext] = None) -> None:
        super().__init__()
        self.context = context or TransformationContext()

    @property
    @abstractmethod
    def name(self) -> str:
        """Return unique string identifier or name of this transformation."""
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Return user-friendly explanation of what this transformation rule accomplishes."""
        raise NotImplementedError

    @abstractmethod
    def can_transform(self, record: Dict[str, Any]) -> bool:
        """Check whether the supplied record is eligible or possesses required fields for this transformation."""
        raise NotImplementedError

    @abstractmethod
    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Apply deterministic mutation or enrichment to the record and return the new dictionary."""
        raise NotImplementedError

    @abstractmethod
    def validate(self, record: Dict[str, Any]) -> List[TransformationError]:
        """Inspect the record against business or schema rules and return a list of validation errors."""
        raise NotImplementedError

    def execute(self, context: MacContext) -> Dict[str, Any]:
        """Execute this transformation inside a standard MAC workflow pipeline context."""
        payload = context.get("payload", {})
        records = payload.get("records")
        if not records:
            single_rec = payload.get("record")
            if single_rec and isinstance(single_rec, dict):
                if not self.can_transform(single_rec):
                    return {"payload": payload}
                errors = self.validate(single_rec)
                if errors:
                    out = dict(payload)
                    out["errors"] = [e.to_dict() for e in errors]
                    return {"payload": out}
                transformed = self.transform(single_rec)
                out = dict(payload)
                out["record"] = transformed
                return {"payload": out}
            return {"payload": payload}

        transformed_list: List[Dict[str, Any]] = []
        all_errors: List[Dict[str, Any]] = []
        for rec in records:
            if not isinstance(rec, dict) or not self.can_transform(rec):
                transformed_list.append(rec)
                continue
            errs = self.validate(rec)
            if errs:
                all_errors.extend([e.to_dict() for e in errs])
                transformed_list.append(rec)
            else:
                transformed_list.append(self.transform(rec))

        out_payload = dict(payload)
        out_payload["records"] = transformed_list
        if all_errors:
            out_payload["errors"] = all_errors
        return {"payload": out_payload}
