import copy
from typing import Any, List, Dict

from apps.data_engine.components.base import BaseComponent, MacContext
from .base import BaseMapper

class DynamicMapper(BaseMapper):
    """Concrete mapper that translates dictionary keys based on a mapping config.
    
    If a key is not in the config, it can either be kept as-is or discarded 
    based on the strict_mapping flag (default is to keep as-is for flexibility).
    """
    
    def __init__(self, strict_mapping: bool = False):
        self.strict_mapping = strict_mapping
        
    def map(self, data: List[Dict[str, Any]], config: Dict[str, str]) -> List[Dict[str, Any]]:
        if not isinstance(data, list):
            raise ValueError("DynamicMapper expects a list of dictionaries")
        if not config:
            # If no mapping config provided, return data as is
            return data
            
        mapped_data = []
        for row in data:
            if not isinstance(row, dict):
                continue
                
            mapped_row = {}
            for key, value in row.items():
                if key in config:
                    mapped_row[config[key]] = value
                elif not self.strict_mapping:
                    mapped_row[key] = value
            mapped_data.append(mapped_row)
            
        return mapped_data

class DynamicMapperComponent(BaseComponent):
    """Adapter to integrate DynamicMapper into the MAC pipeline."""
    component_type = "mapper"
    
    def execute(self, context: MacContext) -> MacContext:
        # Configuration is expected to be passed in context["metadata"]["mapping_config"]
        # Example: {"Nombres": "first_name", "Identificación": "national_id"}
        config = context.get("metadata", {}).get("mapping_config", {})
        
        # Strict mapping flag could also come from metadata, defaulting to False
        strict = context.get("metadata", {}).get("strict_mapping", False)
        
        mapper = DynamicMapper(strict_mapping=strict)
        payload = context.get("payload", [])
        
        context["payload"] = mapper.map(payload, config)
        return context
