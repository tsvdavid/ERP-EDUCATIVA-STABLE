from datetime import date, datetime
from typing import Any, List, Dict, Tuple

from apps.data_engine.components.base import BaseComponent, MacContext
from .base import BaseCaster

class TypeCaster(BaseCaster):
    """Concrete caster that converts strings to native Python types."""
    
    def cast(self, data: List[Dict[str, Any]], schema: Dict[str, str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if not isinstance(data, list):
            raise ValueError("TypeCaster expects a list of dictionaries")
        if not schema:
            return data, []
            
        casted_data = []
        errors = []
        
        for index, row in enumerate(data):
            if not isinstance(row, dict):
                continue
                
            casted_row = {}
            for key, value in row.items():
                target_type = schema.get(key)
                if not target_type or value in (None, ""):
                    casted_row[key] = value
                    continue
                    
                try:
                    if target_type == "int":
                        casted_row[key] = int(value)
                    elif target_type == "float":
                        casted_row[key] = float(value)
                    elif target_type == "bool":
                        casted_row[key] = str(value).lower() in ("true", "1", "t", "yes", "y", "si", "s")
                    elif target_type == "date":
                        # Basic ISO format parser for dates as an example
                        casted_row[key] = date.fromisoformat(str(value))
                    else:
                        # Fallback for unknown types (keep as string)
                        casted_row[key] = str(value)
                except ValueError as e:
                    # Capture casting error but keep the original value
                    casted_row[key] = value
                    errors.append({
                        "row": index,
                        "field": key,
                        "error": f"Failed to cast '{value}' to {target_type}: {str(e)}"
                    })
                    
            casted_data.append(casted_row)
            
        return casted_data, errors

class TypeCasterComponent(BaseComponent):
    """Adapter to integrate TypeCaster into the MAC pipeline."""
    component_type = "caster"
    
    def execute(self, context: MacContext) -> MacContext:
        # Schema configuration expected in metadata
        # Example: {"age": "int", "is_active": "bool", "birth_date": "date"}
        schema = context.get("metadata", {}).get("schema_config", {})
        
        caster = TypeCaster()
        payload = context.get("payload", [])
        
        casted_payload, errors = caster.cast(payload, schema)
        context["payload"] = casted_payload
        
        if errors:
            if "metadata" not in context:
                context["metadata"] = {}
            if "validation_errors" not in context["metadata"]:
                context["metadata"]["validation_errors"] = []
            context["metadata"]["validation_errors"].extend(errors)
            
        return context
