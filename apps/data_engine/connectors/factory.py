# apps/data_engine/connectors/factory.py
"""ConnectorFactory automating creation of external data source connectors."""

from typing import Any, Optional

from .base import BaseConnector
from .contracts import ConnectorConfig
from .registry import ConnectorRegistry


class ConnectorFactory:
    """Factory responsible for instantiating the correct BaseConnector given a configuration."""

    @staticmethod
    def create_connector(
        config: ConnectorConfig,
        registry: Optional[ConnectorRegistry] = None,
    ) -> BaseConnector:
        """Instantiate a connector matching the `connector_type` specified in `config`.

        Parameters
        ----------
        config : ConnectorConfig
            Target configuration specifying `connector_type` and connection parameters.
        registry : Optional[ConnectorRegistry]
            Registry instance to lookup the class from (defaults to global singleton).
        """
        reg = registry or ConnectorRegistry.global_registry()
        cls = reg.get_connector_class(config.connector_type)
        return cls(config=config)

    @staticmethod
    def create_from_params(
        connector_type: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> BaseConnector:
        """Helper to create a connector directly from parameter arguments."""
        config = ConnectorConfig(
            connector_type=connector_type,
            host=host,
            port=port,
            username=username,
            password=password,
            parameters=kwargs,
        )
        return ConnectorFactory.create_connector(config)
