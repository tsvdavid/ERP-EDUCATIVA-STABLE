from typing import Any, List, Dict

from apps.data_engine.components.base import BaseComponent, MacContext
from .base import BaseValidator

class RequiredFieldsValidator(BaseValidator):
    """Validator that ensures required fields are present in the data."""
    
    def __init__(self, required_fields: List[str] = None):
        self.required_fields = required_fields or []
        
    def validate(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        errors = []
        if not self.required_fields:
            return errors
            
        for index, row in enumerate(data):
            for field in self.required_fields:
                if field not in row or row[field] in (None, ""):
                    errors.append({
                        "row": index,
                        "field": field,
                        "error": f"Required field '{field}' is missing or empty."
                    })
        return errors

class RequiredFieldsValidatorComponent(BaseComponent):
    """Adapter to integrate RequiredFieldsValidator into the MAC pipeline."""
    component_type = "validator"
    
    def execute(self, context: MacContext) -> MacContext:
        # In a real scenario, required_fields would come from context metadata or configuration
        required_fields = context.get("metadata", {}).get("required_fields", [])
        validator = RequiredFieldsValidator(required_fields=required_fields)
        
        payload = context.get("payload", [])
        errors = validator.validate(payload)
        
        if errors:
            if "metadata" not in context:
                context["metadata"] = {}
            if "validation_errors" not in context["metadata"]:
                context["metadata"]["validation_errors"] = []
            context["metadata"]["validation_errors"].extend(errors)
            
        return context
