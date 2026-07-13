# apps/data_engine/integration/exceptions.py
"""Domain exceptions for the ERP Integration Layer."""

from apps.data_engine.core.exceptions import MacError


class IntegrationException(MacError):
    """Base exception for all integration-related errors."""


class MappingError(IntegrationException):
    """Raised when record mapping/translation fails."""


class PersistenceError(IntegrationException):
    """Raised when record persistence fails."""


class TransactionError(IntegrationException):
    """Raised when transactional operations fail."""


class AdapterNotFoundError(IntegrationException):
    """Raised when no adapter is found for the given entity name."""
