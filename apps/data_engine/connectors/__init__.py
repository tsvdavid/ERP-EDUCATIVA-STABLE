# apps/data_engine/connectors/__init__.py
"""Connector Framework & External Data Source Integration for MAC (TAREA 25).

Provides a decoupled, Zero-ORM integration layer allowing MAC to ingest data
from files, relational databases, REST APIs, cloud storage, and enterprise
services while strictly adhering to Clean Architecture principles:

    Core ← Components ← Services ← Application ← API
                              ↑
                          Connectors
"""

from .authentication import (
    ApiKeyAuth,
    BaseAuthProvider,
    BasicAuth,
    BearerAuth,
    OAuthProvider,
)
from .base import BaseConnector
from .contracts import ConnectorConfig
from .datasource import DataSource
from .exceptions import (
    AuthenticationException,
    ConnectionFailedException,
    ConnectorException,
    InvalidConfigurationException,
    TimeoutException,
    UnsupportedConnectorException,
)
from .factory import ConnectorFactory
from .registry import ConnectorRegistry

__all__ = [
    "BaseConnector",
    "ConnectorConfig",
    "DataSource",
    "ConnectorRegistry",
    "ConnectorFactory",
    "BaseAuthProvider",
    "BearerAuth",
    "ApiKeyAuth",
    "BasicAuth",
    "OAuthProvider",
    "ConnectorException",
    "ConnectionFailedException",
    "AuthenticationException",
    "UnsupportedConnectorException",
    "TimeoutException",
    "InvalidConfigurationException",
]
