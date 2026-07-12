# apps/data_engine/templates/contracts.py
"""Domain contracts and immutable context DTOs for import templates."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class TemplateContext:
    """Immutable execution context accompanying template instantiation and pipeline execution."""
    tenant_id: Optional[str] = None
    run_id: Optional[str] = None
    template_code: Optional[str] = None
    template_version: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Safe getter for runtime template parameters."""
        return self.parameters.get(key, default)
