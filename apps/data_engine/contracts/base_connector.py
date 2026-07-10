'''Contract for MAC connector base.

The connector abstracts any external data source that the MAC pipeline may need to
communicate with (e.g., a file system, an external API, a message broker). The
contract does **not** implement any concrete logic – it only defines the required
interface for concrete connector implementations.
''' 

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseConnector(ABC):
    """Abstract base class for data source connectors used by the MAC module.

    Implementations must provide a way to establish a connection (if applicable)
    and retrieve data based on a query payload.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection to the external source.

        For stateless sources this may be a no‑op. Implementations should raise
        appropriate exceptions if the connection cannot be established.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch(self, query: Dict[str, Any]) -> Any:
        """Retrieve data from the external source.

        Parameters
        ----------
        query: Dict[str, Any]
            Parameters that define what data should be fetched.

        Returns
        -------
        Any
            The raw data returned by the source; concrete types are defined by
            the implementation.
        """
        raise NotImplementedError
