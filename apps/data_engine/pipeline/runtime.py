# apps/data_engine/pipeline/runtime.py
"""PipelineRuntime container class holding the actual instantiated components."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class PipelineRuntime:
    """Read-only container holding live MAC components for a specific pipeline execution."""

    connector: Any
    template: Optional[Any]
    transformations: Any
    quality_engine: Optional[Any]
    business_engine: Optional[Any]
    workflow: Optional[Any]
    configuration: Dict[str, Any] = field(default_factory=dict)
