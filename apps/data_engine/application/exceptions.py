# apps/data_engine/application/exceptions.py
"""Application layer exceptions for the MAC engine.

All exceptions inherit from ``MacError`` to maintain a consistent error
hierarchy across the entire MAC ecosystem.
"""

from apps.data_engine.core.exceptions import MacError


class ApplicationException(MacError):
    """Base exception for all MAC Application layer errors."""
    pass


class ValidationException(ApplicationException):
    """Raised when pre-import validation checks or data contracts fail."""
    pass


class SessionException(ApplicationException):
    """Raised when session management or state retrieval fails."""
    pass


class ImportException(ApplicationException):
    """Raised when an import workflow fails or cannot be initiated."""
    pass


class ExportException(ApplicationException):
    """Raised when error or data export generation fails."""
    pass


class ServiceUnavailableException(ApplicationException):
    """Raised when a requested application service or dependency cannot be resolved."""
    pass
