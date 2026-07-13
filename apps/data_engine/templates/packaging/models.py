# apps/data_engine/templates/packaging/models.py
"""Immutable data transfer objects representing import template packages."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from apps.data_engine.templates.models import TemplateDefinition, ImportPipelineDefinition


@dataclass(frozen=True)
class PackageMetadata:
    """Metadata detailing the origin, integrity, and identity of a template package bundle."""

    name: str
    version: str
    created_at: str
    author: str
    description: str
    checksum: str = ""
    is_signed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize package metadata to a standard python dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at,
            "author": self.author,
            "description": self.description,
            "checksum": self.checksum,
            "is_signed": self.is_signed,
        }


@dataclass(frozen=True)
class TemplatePackage:
    """Comprehensive representation of a versioned, exportable and importable .macpkg template bundle."""

    metadata: PackageMetadata
    template_definition: TemplateDefinition
    pipeline_definition: ImportPipelineDefinition
    migration_rules: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the complete package including nested metadata, schemas, and configurations."""
        return {
            "metadata": self.metadata.to_dict(),
            "template_definition": self.template_definition.to_dict(),
            "pipeline_definition": self.pipeline_definition.to_dict(),
            "migration_rules": self.migration_rules,
        }
