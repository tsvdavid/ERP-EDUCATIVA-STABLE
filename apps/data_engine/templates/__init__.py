# apps/data_engine/templates/__init__.py
"""Import Template & Declarative Pipeline Definition Framework for MAC (TAREA 27).

Provides an enterprise template engine that encapsulates connectors, column mappings,
transformations, validators, and loader configurations under versioned, reusable,
and declarative templates without hardcoded programmatic logic.
Strictly adheres to Clean Architecture and Zero-ORM in its entirety:

    Connector ↓ Mapping ↓ Validators ↓ Transformations ↓ Loader ↓ Persistence ↓ Reports
"""

from .base import BaseImportTemplate
from .builder import TemplatePipelineBuilder
from .contracts import TemplateContext
from .exceptions import (
    TemplateBuildException,
    TemplateException,
    TemplateNotFoundException,
    TemplateValidationException,
    VersionConflictException,
)
from .models import (
    ColumnDefinition,
    ConnectorDefinition,
    ImportPipelineDefinition,
    LoaderDefinition,
    TemplateDefinition,
    TemplateValidationError,
    TemplateVersion,
    TransformationDefinition,
    ValidatorDefinition,
)
from .registry import TemplateRegistry
from .standard import FinancialFeeTemplate, StudentEnrollmentTemplate

__all__ = [
    "BaseImportTemplate",
    "TemplateContext",
    "TemplateVersion",
    "ColumnDefinition",
    "TemplateDefinition",
    "ConnectorDefinition",
    "TransformationDefinition",
    "ValidatorDefinition",
    "LoaderDefinition",
    "ImportPipelineDefinition",
    "TemplateValidationError",
    "TemplateException",
    "TemplateNotFoundException",
    "TemplateValidationException",
    "TemplateBuildException",
    "VersionConflictException",
    "TemplateRegistry",
    "TemplatePipelineBuilder",
    "StudentEnrollmentTemplate",
    "FinancialFeeTemplate",
]
