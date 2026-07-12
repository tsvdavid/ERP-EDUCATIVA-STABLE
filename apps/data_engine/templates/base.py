# apps/data_engine/templates/base.py
"""Abstract base contract for declarative import templates."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .contracts import TemplateContext
from .models import (
    ImportPipelineDefinition,
    TemplateDefinition,
    TemplateValidationError,
    TemplateVersion,
)


class BaseImportTemplate(ABC):
    """Abstract base class for declarative import templates.

    Encapsulates schema, columns, connectors, transformations, validators, and
    loader specifications under a versioned, reusable template contract.
    """

    def __init__(self, context: Optional[TemplateContext] = None) -> None:
        self.context = context or TemplateContext()

    @property
    @abstractmethod
    def code(self) -> str:
        """Return unique string code identifying the template family."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Return user-friendly name of the import template."""
        raise NotImplementedError

    @property
    @abstractmethod
    def version(self) -> TemplateVersion:
        """Return semantic version descriptor of this template specification."""
        raise NotImplementedError

    @abstractmethod
    def get_template_definition(self) -> TemplateDefinition:
        """Return structural metadata and column schema definition."""
        raise NotImplementedError

    @abstractmethod
    def get_pipeline_definition(self) -> ImportPipelineDefinition:
        """Return declarative pipeline stages (connector, mapping, transformations, validators, loader)."""
        raise NotImplementedError

    @abstractmethod
    def validate_template(self) -> List[TemplateValidationError]:
        """Perform self-diagnostic structural validation on the template configuration."""
        raise NotImplementedError

    def can_handle(self, metadata: Dict[str, Any]) -> bool:
        """Determine whether this template is compatible with the supplied source metadata."""
        target_entity = self.get_template_definition().target_entity
        if "entity" in metadata and target_entity:
            return str(metadata["entity"]).lower() == target_entity.lower()
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete template and pipeline definition to dictionary."""
        return {
            "code": self.code,
            "name": self.name,
            "version": str(self.version),
            "definition": self.get_template_definition().to_dict(),
            "pipeline": self.get_pipeline_definition().to_dict(),
        }
