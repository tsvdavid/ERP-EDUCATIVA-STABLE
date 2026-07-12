# apps/data_engine/connectors/contracts.py
"""Domain contracts and immutable DTOs for data source connectors."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .authentication import BaseAuthProvider


@dataclass(frozen=True)
class ConnectorConfig:
    """Immutable configuration DTO encapsulating parameters to connect to external data sources."""
    connector_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl: bool = False
    timeout: int = 30
    parameters: Dict[str, Any] = field(default_factory=dict)
    auth_provider: Optional["BaseAuthProvider"] = None

    def get_param(self, key: str, default: Any = None) -> Any:
        """Helper to retrieve custom parameters cleanly."""
        return self.parameters.get(key, default)
