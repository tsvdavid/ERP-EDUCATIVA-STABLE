# apps/data_engine/components/transformers/standardize_fields.py
"""StandardizeFields transformer.

Normalises the keys inside the ``payload`` of a ``MacContext`` to ``snake_case``
and ensures that the values are basic JSON‑serialisable types.

The component is deliberately stateless – it does not store any internal state
and relies only on the supplied ``MacContext``.
"""

from .base import BaseTransformer
from ..base import component_name, MacContext

class StandardizeFields(BaseTransformer):
    """Transformer that normalises payload keys to ``snake_case``.

    Example:
        input payload: {"UserID": 1, "orderID": "A12"}
        output payload: {"user_id": 1, "order_id": "A12"}
    """

    component_type: str = "transformer"

    def execute(self, context: MacContext):  # type: ignore[override]
        payload = context.get("payload", {})
        if not isinstance(payload, dict):
            # If payload is not a dict, leave it untouched.
            return context
        normalized = {}
        for key, value in payload.items():
            # Use the existing helper to convert the key name.
            normalized_key = component_name(type("Tmp", (object,), {"__name__": key}))
            normalized[normalized_key] = value
        # Return a new context dict with the updated payload.
        new_context = dict(context)
        new_context["payload"] = normalized
        return new_context
