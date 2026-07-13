# apps/data_engine/pipeline/models.py
"""Immutable DTO models representing pipeline definitions and execution reports."""

from dataclasses import dataclass, field, asdict
import json
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PipelineDefinition:
    """Immutable data transfer object defining a full data ingestion/transformation pipeline."""

    pipeline_id: str
    name: str
    version: str
    connector: Dict[str, Any]
    template: Optional[str] = None
    transformations: List[Dict[str, Any]] = field(default_factory=list)
    quality_rules: List[Dict[str, Any]] = field(default_factory=list)
    business_rules: List[Dict[str, Any]] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineDefinition":
        """Instantiate a PipelineDefinition from a dictionary."""
        return cls(
            pipeline_id=data["pipeline_id"],
            name=data["name"],
            version=data["version"],
            connector=data["connector"],
            template=data.get("template"),
            transformations=data.get("transformations") or [],
            quality_rules=data.get("quality_rules") or [],
            business_rules=data.get("business_rules") or [],
            options=data.get("options") or {},
        )

    @classmethod
    def from_json(cls, json_str: str) -> "PipelineDefinition":
        """Instantiate a PipelineDefinition from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Convert the PipelineDefinition to a dictionary representation."""
        return asdict(self)


@dataclass(frozen=True)
class PipelineExecutionReport:
    """Immutable report containing the metrics and logs of a pipeline run."""

    pipeline_id: str
    run_id: str
    start_time: str
    finish_time: str
    duration: float
    processed: int
    accepted: int
    rejected: int
    quality_score: float
    business_violations: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the report to a dictionary representation."""
        return asdict(self)
