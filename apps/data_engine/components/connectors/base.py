# apps/data_engine/components/connectors/base.py
"""Base classes for MAC connectors.

Connectors are responsible for retrieving data from external systems (files,
services, etc.). They follow the same contract as other MAC components.
"""

from abc import ABC
from .base import BaseComponent, component_name

class BaseConnector(BaseComponent, ABC):
    """Abstract base for all connector components.

    Sub‑classes must implement ``execute(self, context)`` and should expose a
    ``component_type`` attribute with the value ``"connector"`` so that the
    orchestrator can log the component type.
    """

    component_type: str = "connector"

    # No additional abstract methods are required – ``execute`` is already
    # defined abstract in ``BaseComponent``.
