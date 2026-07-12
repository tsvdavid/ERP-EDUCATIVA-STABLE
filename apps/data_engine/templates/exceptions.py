# apps/data_engine/templates/exceptions.py
"""Domain exception hierarchy for the MAC Template Engine."""

from apps.data_engine.core.exceptions import MacError


class TemplateException(MacError):
    """Base exception for all import template and declarative pipeline definition errors."""
    pass


class TemplateNotFoundException(TemplateException):
    """Raised when requesting a template code or version that is not registered in TemplateRegistry."""
    pass


class TemplateValidationException(TemplateException):
    """Raised when structural schema checks or validation rules fail on a template definition."""
    pass


class TemplateBuildException(TemplateException):
    """Raised when TemplatePipelineBuilder fails to instantiate connectors or transformation pipelines."""
    pass


class VersionConflictException(TemplateException):
    """Raised when attempting to register a template version that collides with existing immutable records."""
    pass
