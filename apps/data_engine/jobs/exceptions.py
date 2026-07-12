# apps/data_engine/jobs/exceptions.py
"""Domain Exceptions for Background Processing & Distributed Job Framework (TAREA 24).

All exceptions inherit from `MacError` for unified domain error interception and API mapping.
"""

from typing import Any, List, Optional
from apps.data_engine.core.exceptions import MacError


class JobException(MacError):
    """Base exception for all background job failures and state violations."""
    def __init__(self, message: str, violations: Optional[List[Any]] = None):
        super().__init__(message)
        self.message = message
        self.violations = violations or []


class JobNotFoundException(JobException):
    """Raised when a requested job record cannot be located in storage."""
    pass


class JobCancelledException(JobException):
    """Raised when attempting to execute or modify a job that has been cancelled or revoked."""
    pass


class JobRetryExceededException(JobException):
    """Raised when a job fails and has exhausted all configured automatic retries."""
    pass
