from typing import Any, List, Dict

from apps.data_engine.components.base import BaseComponent, MacContext
from .base import BaseValidator

class EmptyRowsValidator(BaseValidator):
    """Validator that checks if rows are completely empty."""
    
    def validate(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        errors = []
        for index, row in enumerate(data):
            # A row is considered empty if all its string values are empty/whitespace 
            # or if it has no values at all.
            is_empty = True
            for value in row.values():
                if value is not None and str(value).strip() != "":
                    is_empty = False
                    break
                    
            if is_empty:
                errors.append({
                    "row": index,
                    "error": "Row is completely empty."
                })
        return errors

class EmptyRowsValidatorComponent(BaseComponent):
    """Adapter to integrate EmptyRowsValidator into the MAC pipeline."""
    component_type = "validator"
    
    def execute(self, context: MacContext) -> MacContext:
        validator = EmptyRowsValidator()
        payload = context.get("payload", [])
        errors = validator.validate(payload)
        
        if errors:
            if "metadata" not in context:
                context["metadata"] = {}
            if "validation_errors" not in context["metadata"]:
                context["metadata"]["validation_errors"] = []
            context["metadata"]["validation_errors"].extend(errors)
            
        return context
