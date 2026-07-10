# apps/data_engine/components/extractor.py
"""CSVExtractor component – simulated CSV data extraction.

The component does **not** read real files; it returns a static payload
representing what a CSV file could contain.  This keeps the implementation
lightweight and free of external dependencies.
"""

from .base import BaseComponent, MacContext


class CSVExtractor(BaseComponent):
    """Simulated extractor that returns a fixed payload.

    The payload mimics a list of dictionaries as if rows were read from a
    CSV.  The actual content is irrelevant for the current stage – the
    focus is on the contract and integration with the orchestrator.
    """

    def execute(self, context: MacContext) -> dict:
        # In a real implementation we would read a CSV file here.
        # For the audit we return a deterministic static structure.
        data = {
            "records": [
                {"id": 1, "value": "alpha"},
                {"id": 2, "value": "beta"},
            ]
        }
        # Merge with any existing payload so downstream components can see it.
        payload = context.get("payload", {})
        payload.update(data)
        return {"payload": payload}
