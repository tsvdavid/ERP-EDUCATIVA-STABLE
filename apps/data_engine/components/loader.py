# apps/data_engine/components/loader.py
"""MemoryLoader component – dummy loader that simulates storing data.

The component receives the current ``payload`` via the context and returns a
simple status indicating the data was "loaded". No external resources are used.
"""

from typing import Dict, Any

from .base import BaseComponent, MacContext


class MemoryLoader(BaseComponent):
    """Placeholder loader that pretends to persist the payload.

    It does not modify the payload; it merely returns a dict with a ``status``
    key. In a real implementation this would write to a database or cache.
    """

    def execute(self, context: MacContext) -> Dict[str, Any]:
        # No actual I/O – just acknowledge receipt.
        return {"status": "payload loaded into memory"}
