# apps/data_engine/api/exceptions.py
"""Custom DRF Exception Handler for the MAC API Gateway.

Interprets MAC domain and application layer exceptions (`application/exceptions.py`
and `core/exceptions.py`) and maps them to standardized, clean HTTP JSON responses
with appropriate status codes.
"""

from typing import Any, Dict, Optional
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from apps.data_engine.application.exceptions import (
    ApplicationException,
    ImportException,
    ServiceUnavailableException,
    SessionException,
    ValidationException,
)
from apps.data_engine.core.exceptions import MacError


class TenantIsolationViolation(Exception):
    """Raised when an authenticated user attempts to access a tenant ID outside their scope."""
    pass


def custom_mac_exception_handler(exc: Exception, context: Dict[str, Any]) -> Optional[Response]:
    """Intercept MAC domain exceptions and format them as DRF Responses."""
    # First, let standard DRF exception handler process DRF exceptions (ValidationError, PermissionDenied, etc.)
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, TenantIsolationViolation):
        return Response(
            {
                "error_code": "TENANT_ISOLATION_VIOLATION",
                "message": str(exc),
                "detail": "Cross-tenant access denied by MAC Gateway.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, ValidationException):
        return Response(
            {
                "error_code": "MAC_VALIDATION_ERROR",
                "message": str(exc),
                "detail": getattr(exc, "violations", []),
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY if hasattr(status, "HTTP_422_UNPROCESSABLE_ENTITY") else status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, SessionException):
        msg = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "not found" in msg.lower() else status.HTTP_409_CONFLICT
        return Response(
            {
                "error_code": "MAC_SESSION_ERROR",
                "message": msg,
            },
            status=status_code,
        )

    if isinstance(exc, ImportException):
        msg = str(exc)
        status_code = status.HTTP_409_CONFLICT if "terminal state" in msg.lower() else status.HTTP_400_BAD_REQUEST
        return Response(
            {
                "error_code": "MAC_IMPORT_ERROR",
                "message": msg,
            },
            status=status_code,
        )

    if isinstance(exc, ServiceUnavailableException):
        return Response(
            {
                "error_code": "MAC_SERVICE_UNAVAILABLE",
                "message": str(exc),
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if isinstance(exc, (ApplicationException, MacError)):
        return Response(
            {
                "error_code": "MAC_GENERAL_ERROR",
                "message": str(exc),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Let unhandled unexpected exceptions bubble up to Django/WSGI 500 handler
    return None
