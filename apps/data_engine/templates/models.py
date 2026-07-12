# apps/data_engine/templates/models.py
"""Immutable domain models and declarative definition DTOs for the Template Engine."""

from dataclasses import dataclass, field
import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TemplateVersion:
    """Semantic versioning descriptor for import templates."""
    major: int
    minor: int
    patch: int
    status: str = "ACTIVE"  # DRAFT, ACTIVE, DEPRECATED, ARCHIVED
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat()[:10])
    changelog: str = ""

    def __str__(self) -> str:
        """Return canonical version string format (e.g., '1.0.0')."""
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, version_str: str, status: str = "ACTIVE") -> "TemplateVersion":
        """Parse version string 'X.Y.Z' into a TemplateVersion object."""
        parts = version_str.strip().split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"Invalid semantic version string: '{version_str}'. Expected 'X.Y.Z'.")
        return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]), status=status)


@dataclass(frozen=True)
class ColumnDefinition:
    """Schema specification for a single import template column or attribute."""
    name: str
    source_field: str
    data_type: str = "str"  # str, int, float, Decimal, bool, date, datetime
    required: bool = False
    default_value: Any = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize column specification to dictionary."""
        return {
            "name": self.name,
            "source_field": self.source_field,
            "data_type": self.data_type,
            "required": self.required,
            "default_value": self.default_value,
            "description": self.description,
        }


@dataclass(frozen=True)
class TemplateDefinition:
    """Metadata and structural column configuration for an import template."""
    code: str
    name: str
    version: TemplateVersion
    columns: List[ColumnDefinition]
    target_entity: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize template definition to dictionary."""
        return {
            "code": self.code,
            "name": self.name,
            "version": str(self.version),
            "version_status": self.version.status,
            "columns": [col.to_dict() for col in self.columns],
            "target_entity": self.target_entity,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ConnectorDefinition:
    """Declarative configuration specifying external data source connector."""
    connector_type: str  # csv, json, excel, sql, rest
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize connector specification to dictionary."""
        return {
            "connector_type": self.connector_type,
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True)
class TransformationDefinition:
    """Declarative configuration specifying a transformation step."""
    transformation_type: str  # rename_fields, type_cast, trim, uppercase, regex_replace, lookup, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize transformation step to dictionary."""
        return {
            "transformation_type": self.transformation_type,
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True)
class ValidatorDefinition:
    """Declarative configuration specifying a validation rule."""
    validator_type: str  # required_validator, regex_validator, range_validator, unique_validator, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize validator specification to dictionary."""
        return {
            "validator_type": self.validator_type,
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True)
class LoaderDefinition:
    """Declarative configuration specifying destination loading and persistence parameters."""
    loader_type: str = "default"
    target_table: str = ""
    batch_size: int = 1000
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize loader parameters to dictionary."""
        return {
            "loader_type": self.loader_type,
            "target_table": self.target_table,
            "batch_size": self.batch_size,
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True)
class ImportPipelineDefinition:
    """Master specification combining all stages into an executable ETL pipeline definition."""
    connector: ConnectorDefinition
    mapping: Dict[str, str] = field(default_factory=dict)
    transformations: List[TransformationDefinition] = field(default_factory=list)
    validators: List[ValidatorDefinition] = field(default_factory=list)
    loader: LoaderDefinition = field(default_factory=lambda: LoaderDefinition("default", ""))
    options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete import pipeline specification to dictionary."""
        return {
            "connector": self.connector.to_dict(),
            "mapping": dict(self.mapping),
            "transformations": [t.to_dict() for t in self.transformations],
            "validators": [v.to_dict() for v in self.validators],
            "loader": self.loader.to_dict(),
            "options": dict(self.options),
        }


@dataclass(frozen=True)
class TemplateValidationError:
    """Diagnostic error returned during structural schema validation of a template."""
    code: str
    message: str
    template_code: str
    field: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize diagnostic error to dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "template_code": self.template_code,
            "field": self.field,
        }
