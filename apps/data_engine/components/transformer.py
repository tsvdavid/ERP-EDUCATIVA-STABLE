# apps/data_engine/components/transformer.py
"""StandardizeTransformer component – simple payload transformation.

For demonstration purposes this component upper‑cases all string values in the
payload under the ``records`` key.
"""

from typing import Any, List, Dict

from .base import BaseComponent, MacContext


class StandardizeTransformer(BaseComponent):
    """Transform payload records to a standardized format.

    The implementation expects the context to contain a ``payload`` dict with a
    ``records`` list of dictionaries. Each record's string values are upper‑cased.
    """

    def execute(self, context: MacContext) -> Dict[str, Any]:
        payload = context.get("payload", {})
        records: List[Dict[str, Any]] = payload.get("records", [])
        for record in records:
            for key, value in record.items():
                if isinstance(value, str):
                    record[key] = value.upper()
        return {"payload": payload}
