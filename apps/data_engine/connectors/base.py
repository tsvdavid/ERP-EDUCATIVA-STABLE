# apps/data_engine/connectors/base.py
"""Abstract base class for all external data source connectors.

Connectors are decoupled integration components responsible for establishing
connections, authenticating, testing connectivity, retrieving metadata, and
fetching or streaming raw records (`List[Dict[str, Any]]`) from external systems.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional

from apps.data_engine.components.base import BaseComponent, MacContext
from .contracts import ConnectorConfig
from .datasource import DataSource


class BaseConnector(BaseComponent, ABC):
    """Abstract contract for enterprise external data source connectors.

    Every concrete connector must implement the lifecycle and retrieval methods:
    `connect()`, `disconnect()`, `test_connection()`, `fetch()`, `stream()`, and `metadata()`.
    """

    component_type: str = "connector"

    def __init__(self, config: Optional[ConnectorConfig] = None) -> None:
        super().__init__()
        self.config = config or ConnectorConfig(connector_type="unknown")
        self._is_connected: bool = False

    @property
    def is_connected(self) -> bool:
        """Return True if the active connection to the external data source is established."""
        return self._is_connected

    @abstractmethod
    def connect(self) -> None:
        """Establish connection or initialize resources with the external data source."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """Close active connections and release associated system/network resources."""
        raise NotImplementedError

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify if the external data source is reachable and credentials are valid.

        Returns
        -------
        bool
            True if connection and authentication succeed, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch(
        self,
        query_or_path: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Retrieve rows or records synchronously as a list of dictionaries.

        Parameters
        ----------
        query_or_path : Optional[str]
            SQL query, API endpoint path, or file path to fetch from.
        limit : Optional[int]
            Maximum number of records to return.
        """
        raise NotImplementedError

    @abstractmethod
    def stream(
        self,
        query_or_path: Optional[str] = None,
        chunk_size: int = 1000,
        **kwargs: Any,
    ) -> Iterator[List[Dict[str, Any]]]:
        """Stream data in batches (`chunk_size`) to support large-scale imports.

        Parameters
        ----------
        query_or_path : Optional[str]
            SQL query, API endpoint path, or file path to stream from.
        chunk_size : int
            Number of records per batch yielded by the iterator.
        """
        raise NotImplementedError

    @abstractmethod
    def metadata(self) -> DataSource:
        """Inspect the external data source and return schema and metadata snapshot."""
        raise NotImplementedError

    def execute(self, context: MacContext) -> Dict[str, Any]:
        """Execute connector retrieval within a standard MAC pipeline workflow.

        Automates `connect() -> fetch() -> disconnect()` and injects raw data
        and metadata into the workflow context payload.
        """
        payload = context.get("payload", {})
        query_or_path = payload.get("source") or self.config.parameters.get("source")
        limit = payload.get("limit") or self.config.parameters.get("limit")

        try:
            if not self.is_connected:
                self.connect()

            records = self.fetch(query_or_path=query_or_path, limit=limit)
            meta = self.metadata()

            out_payload = dict(payload)
            out_payload["raw_data"] = records
            out_payload["source_metadata"] = meta.to_dict()
            return {"payload": out_payload}
        finally:
            if self.is_connected:
                self.disconnect()
