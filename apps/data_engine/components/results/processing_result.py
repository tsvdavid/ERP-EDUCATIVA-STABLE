from typing import Any, List, Dict
from dataclasses import dataclass, field

@dataclass
class ProcessingResult:
    """Represents the final result of a MAC processing pipeline.
    
    Attributes:
        success: Whether the processing succeeded without critical errors.
        data: The processed payload (List of dictionaries).
        errors: A list of validation errors found during processing.
        metadata: Additional context or metrics from the pipeline.
    """
    success: bool = True
    data: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_context(cls, context: dict) -> "ProcessingResult":
        """Creates a ProcessingResult from a MacContext dictionary."""
        payload = context.get("payload", [])
        if not isinstance(payload, list):
            payload = []
            
        metadata = context.get("metadata", {})
        errors = metadata.get("validation_errors", [])
        
        # Consider it successful if there are no validation errors, 
        # or you can define your own success criteria.
        success = len(errors) == 0
        
        return cls(
            success=success,
            data=payload,
            errors=errors,
            metadata=metadata
        )
