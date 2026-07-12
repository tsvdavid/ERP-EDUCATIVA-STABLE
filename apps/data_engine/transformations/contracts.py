# apps/data_engine/transformations/contracts.py
"""Domain contracts and immutable context DTOs for data transformations."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class TransformationContext:
    """Immutable execution context accompanying records through the transformation pipeline."""
    tenant_id: Optional[str] = None
    run_id: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Safe getter for runtime transformation variables."""
        return self.variables.get(key, default)
