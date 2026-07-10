"""Base component for MAC.

All MAC components inherit from :class:`BaseComponent` which itself
inherits from the generic ``BaseService`` defined in
``apps.data_engine.services.base``.  The contract is a single ``execute``
method that receives a ``MacContext`` (a ``TypedDict``) and returns any
value.
"""

from typing import TypedDict, Any
from abc import ABC, abstractmethod

from apps.data_engine.services.base import BaseService


class MacContext(TypedDict, total=False):
    tenant_id: str
    run_id: str
    user_id: str
    payload: dict
    metadata: dict


class BaseComponent(BaseService, ABC):
    """Abstract base for all MAC processing components.

    Sub‑classes must implement ``execute(self, context: MacContext)``.
    """

    @abstractmethod
    def execute(self, context: MacContext) -> Any:  # pragma: no cover
        """Process the supplied *context* and return a result.
        """
        raise NotImplementedError


def component_name(cls: type) -> str:
    """Return a snake_case name derived from the class name."""
    import re
    name = getattr(cls, "__name__", str(cls))
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


__all__ = ["MacContext", "BaseComponent", "component_name"]
