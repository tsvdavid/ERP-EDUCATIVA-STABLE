# apps/data_engine/pipeline/exceptions.py
"""Domain exceptions for Pipeline Definition & Execution Framework."""

from apps.data_engine.core.exceptions import MacError


class PipelineException(MacError):
    """Base exception for all pipeline-related errors."""


class PipelineBuildError(PipelineException):
    """Raised when pipeline instantiation or validation fails."""


class PipelineExecutionError(PipelineException):
    """Raised when executing a pipeline runtime fails."""
