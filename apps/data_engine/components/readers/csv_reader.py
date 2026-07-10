import csv
import io
from typing import Any, List, Dict

from apps.data_engine.components.base import BaseComponent, MacContext
from .base import BaseReader

class CSVReader(BaseReader):
    """Concrete reader that reads a CSV string into a list of dictionaries."""
    
    def read(self, source: Any) -> List[Dict[str, Any]]:
        if not isinstance(source, str):
            raise ValueError("CSVReader expects a string source")
        
        f = io.StringIO(source)
        reader = csv.DictReader(f)
        return list(reader)

class CSVReaderComponent(BaseComponent):
    """Adapter to integrate CSVReader into the MAC pipeline."""
    component_type = "reader"
    
    def execute(self, context: MacContext) -> MacContext:
        reader = CSVReader()
        source = context.get("payload", "")
        # By convention, if payload is not a string, we might try to extract the source
        # but in this mock layer, we assume payload is the raw string initially.
        if not isinstance(source, str):
            # In a real pipeline, the connector might put the raw string in context['payload']
            source = str(source)
        
        context["payload"] = reader.read(source)
        return context
