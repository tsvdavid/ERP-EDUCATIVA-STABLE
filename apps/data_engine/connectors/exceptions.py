# apps/data_engine/connectors/exceptions.py
"""Domain exception hierarchy for external data source connectors."""

from apps.data_engine.core.exceptions import ConnectorError, MacError


class ConnectorException(ConnectorError):
    """Base exception for all connector and external data source errors."""
    pass


class ConnectionFailedException(ConnectorException):
    """Raised when a connector fails to establish a network or file connection."""
    pass


class AuthenticationException(ConnectorException):
    """Raised when authentication credentials or tokens are rejected by the external source."""
    pass


class UnsupportedConnectorException(ConnectorException):
    """Raised when requesting a connector type that is not registered in the ConnectorRegistry."""
    pass


class TimeoutException(ConnectorException):
    """Raised when a query, network request, or streaming batch exceeds the timeout limit."""
    pass


class InvalidConfigurationException(ConnectorException):
    """Raised when a ConnectorConfig is missing required parameters or is misconfigured."""
    pass
