# apps/data_engine/transformations/__init__.py
"""Transformation Pipeline & Data Processing Framework for MAC (TAREA 26).

Provides an enterprise ETL transformation engine that converts data from any
external connector into clean, validated records ready for MAC staging and loading.
Strictly adheres to Clean Architecture and Zero-ORM in its entirety:

    Core ↓ Components ↓ Connectors ↓ Transformation Pipeline ↓ Workflow ↓ Persistence
"""

from .base import BaseTransformation
from .contracts import TransformationContext
from .exceptions import (
    ExpressionException,
    PipelineException,
    ProcessorException,
    TransformationException,
    ValidationException,
)
from .expressions import ExpressionEngine
from .models import (
    TransformationError,
    TransformationReport,
    TransformationResult,
    TransformationStatistics,
)
from .pipeline import TransformationPipeline
from .processors import (
    DefaultValueProcessor,
    LowerCaseProcessor,
    LookupProcessor,
    RegexProcessor,
    RemoveFieldsProcessor,
    RenameFieldsProcessor,
    TrimProcessor,
    TypeCastProcessor,
    UpperCaseProcessor,
)
from .registry import TransformationRegistry
from .validators import (
    CustomValidator,
    EnumValidator,
    LengthValidator,
    RangeValidator,
    RegexValidator,
    RequiredValidator,
    UniqueValidator,
)

__all__ = [
    "BaseTransformation",
    "TransformationContext",
    "TransformationError",
    "TransformationResult",
    "TransformationReport",
    "TransformationStatistics",
    "TransformationException",
    "ExpressionException",
    "ValidationException",
    "ProcessorException",
    "PipelineException",
    "TransformationRegistry",
    "TransformationPipeline",
    "ExpressionEngine",
    "RenameFieldsProcessor",
    "RemoveFieldsProcessor",
    "TypeCastProcessor",
    "DefaultValueProcessor",
    "TrimProcessor",
    "UpperCaseProcessor",
    "LowerCaseProcessor",
    "RegexProcessor",
    "LookupProcessor",
    "RequiredValidator",
    "RegexValidator",
    "RangeValidator",
    "UniqueValidator",
    "LengthValidator",
    "EnumValidator",
    "CustomValidator",
]
