# apps/data_engine/application/base.py
"""Base abstractions and context helpers for the MAC Application Layer.

Provides clean separation of infrastructure dependencies from application use
cases.
"""

from typing import Any, Dict, Optional


class ApplicationContext:
    """Read-only container for application-level execution metadata."""

    def __init__(self, tenant_id: str, user_id: str, extra: Optional[Dict[str, Any]] = None):
        self._tenant_id = tenant_id
        self._user_id = user_id
        self._extra = dict(extra) if extra else {}

    @property
    def tenant_id(self) -> str:
        return self._tenant_id

    @property
    def user_id(self) -> str:
        return self._user_id

    def get(self, key: str, default: Any = None) -> Any:
        return self._extra.get(key, default)
