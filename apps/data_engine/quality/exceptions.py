# apps/data_engine/quality/exceptions.py
"""Domain exceptions for the Data Quality Rules Engine."""

from apps.data_engine.core.exceptions import MacError


class QualityException(MacError):
    """Base exception for all data quality operations."""
    pass


class RuleException(QualityException):
    """Raised when quality rule evaluation fails due to invalid parameters or runtime exceptions."""
    pass


class ScoringException(QualityException):
    """Raised when quality score calculations fail."""
    pass


class ReportingException(QualityException):
    """Raised when a reporter fails to serialize quality reports."""
    pass
