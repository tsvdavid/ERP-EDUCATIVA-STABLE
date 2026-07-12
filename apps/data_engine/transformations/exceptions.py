# apps/data_engine/transformations/exceptions.py
"""Domain exception hierarchy for the MAC Transformation Engine."""

from apps.data_engine.core.exceptions import MacError


class TransformationException(MacError):
    """Base exception for all transformation and ETL data processing errors."""
    pass


class ExpressionException(TransformationException):
    """Raised when an expression syntax error or evaluation failure occurs in ExpressionEngine."""
    pass


class ValidationException(TransformationException):
    """Raised when critical validation checks fail during transformation."""
    pass


class ProcessorException(TransformationException):
    """Raised when a processor fails to mutate or cast field values."""
    pass


class PipelineException(TransformationException):
    """Raised for sequential composition, dependency, or execution errors inside TransformationPipeline."""
    pass
