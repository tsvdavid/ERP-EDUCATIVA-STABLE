# apps/data_engine/quality/registry.py
"""Central, thread-safe registry to store and resolve quality rules."""

import threading
from typing import Dict, List, Optional
from apps.data_engine.quality.base import BaseQualityRule


class QualityRuleRegistry:
    """Thread-safe registry managing template quality rules."""

    _instance: Optional["QualityRuleRegistry"] = None
    _singleton_lock = threading.Lock()

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rules: Dict[str, BaseQualityRule] = {}

    @classmethod
    def global_registry(cls) -> "QualityRuleRegistry":
        """Return the global thread-safe singleton instance of QualityRuleRegistry."""
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register(self, rule: BaseQualityRule, overwrite: bool = True) -> None:
        """Register a quality rule instance."""
        if not rule or not rule.code:
            raise ValueError("Rule code cannot be empty.")
        with self._lock:
            if rule.code in self._rules and not overwrite:
                raise ValueError(f"Rule '{rule.code}' is already registered.")
            self._rules[rule.code] = rule

    def get(self, code: str) -> BaseQualityRule:
        """Retrieve a quality rule by its unique code identifier."""
        with self._lock:
            if code not in self._rules:
                raise KeyError(f"Quality rule '{code}' not found in registry.")
            return self._rules[code]

    def list_rules(self) -> List[BaseQualityRule]:
        """Return a copy list of all registered quality rules."""
        with self._lock:
            return list(self._rules.values())

    def remove(self, code: str) -> None:
        """Remove a quality rule from the registry."""
        with self._lock:
            self._rules.pop(code, None)

    def reset(self) -> None:
        """Clear all registered rules."""
        with self._lock:
            self._rules.clear()
