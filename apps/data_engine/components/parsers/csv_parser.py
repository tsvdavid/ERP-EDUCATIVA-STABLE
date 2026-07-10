import copy
from typing import Any, List, Dict

from apps.data_engine.components.base import BaseComponent, MacContext
from .base import BaseParser

class CSVParser(BaseParser):
    """Concrete parser that interprets CSV data.
    
    In this minimal implementation, it strips leading and trailing 
    whitespace from all string values.
    """
    
    def parse(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not isinstance(data, list):
            raise ValueError("CSVParser expects a list of dictionaries")
            
        parsed_data = []
        for row in data:
            if not isinstance(row, dict):
                continue
                
            parsed_row = {}
            for key, value in row.items():
                if isinstance(value, str):
                    parsed_row[key] = value.strip()
                else:
                    parsed_row[key] = value
            parsed_data.append(parsed_row)
            
        return parsed_data

class CSVParserComponent(BaseComponent):
    """Adapter to integrate CSVParser into the MAC pipeline."""
    component_type = "parser"
    
    def execute(self, context: MacContext) -> MacContext:
        parser = CSVParser()
        payload = context.get("payload", [])
        context["payload"] = parser.parse(payload)
        return context
