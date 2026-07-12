# apps/data_engine/connectors/datasource.py
"""Pure domain model representing metadata and schema of an external data source."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DataSource:
    """Immutable model describing the schema, metadata, and attributes of a data source.

    Returned by `BaseConnector.metadata()` without requiring ORM or database access.
    """
    name: str
    source_type: str
    columns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    encoding: str = "utf-8"
    dialect: Optional[str] = None
    size_bytes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert DataSource representation to a dictionary for payload serialization."""
        return {
            "name": self.name,
            "source_type": self.source_type,
            "columns": list(self.columns),
            "metadata": dict(self.metadata),
            "encoding": self.encoding,
            "dialect": self.dialect,
            "size_bytes": self.size_bytes,
        }
