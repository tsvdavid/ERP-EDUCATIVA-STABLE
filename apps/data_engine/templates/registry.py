# apps/data_engine/templates/registry.py
"""Thread-safe TemplateRegistry administering versioned import templates."""

import threading
from typing import Dict, List, Optional, Tuple

from .base import BaseImportTemplate
from .exceptions import TemplateNotFoundException, VersionConflictException


class TemplateRegistry:
    """Singleton thread-safe registry managing declarative import templates by code and version."""

    _instance: Optional["TemplateRegistry"] = None
    _singleton_lock = threading.Lock()

    def __init__(self) -> None:
        # Key: (code_lower, version_str) -> BaseImportTemplate
        self._templates: Dict[Tuple[str, str], BaseImportTemplate] = {}
        # Key: code_lower -> active_version_str
        self._active_versions: Dict[str, str] = {}
        self._lock = threading.Lock()

    @classmethod
    def global_registry(cls) -> "TemplateRegistry":
        """Return the global singleton TemplateRegistry instance."""
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_global_registry(cls) -> None:
        """Reset the global singleton registry (for isolated unit testing)."""
        with cls._singleton_lock:
            cls._instance = None

    def register(self, template: BaseImportTemplate, set_active: bool = False, overwrite: bool = False) -> None:
        """Register an import template instance.

        If `set_active` is True (or if no version is yet active for this code),
        the template's version becomes the default active version for the code.
        If `overwrite` is False and the version already exists, raises VersionConflictException.
        """
        if not isinstance(template, BaseImportTemplate):
            raise TypeError(f"{template} must be an instance of BaseImportTemplate.")

        code_key = template.code.lower()
        ver_str = str(template.version)
        key = (code_key, ver_str)

        with self._lock:
            if not overwrite and key in self._templates:
                raise VersionConflictException(
                    f"Template '{template.code}' version '{ver_str}' is already registered."
                )
            self._templates[key] = template
            if set_active or code_key not in self._active_versions:
                self._active_versions[code_key] = ver_str

    def get(self, code: str, version: Optional[str] = None) -> BaseImportTemplate:
        """Retrieve the registered import template for the given code and optional version."""
        code_key = code.lower()
        with self._lock:
            if version is None:
                ver_str = self._active_versions.get(code_key)
                if ver_str is None:
                    raise TemplateNotFoundException(f"No active template registered for code '{code}'.")
            else:
                ver_str = version

            item = self._templates.get((code_key, ver_str))
        if item is None:
            raise TemplateNotFoundException(f"Template '{code}' version '{ver_str}' not found in registry.")
        return item

    def list_templates(self, status: Optional[str] = None) -> List[BaseImportTemplate]:
        """Return a list of registered import templates, optionally filtered by status."""
        with self._lock:
            items = list(self._templates.values())
        if status is not None:
            items = [t for t in items if t.version.status.upper() == status.upper()]
        return sorted(items, key=lambda t: (t.code.lower(), str(t.version)))

    def set_active_version(self, code: str, version: str) -> None:
        """Promote a specific registered version to be the active/default canonical version."""
        code_key = code.lower()
        key = (code_key, version)
        with self._lock:
            if key not in self._templates:
                raise TemplateNotFoundException(
                    f"Cannot set active version: template '{code}' version '{version}' not registered."
                )
            self._active_versions[code_key] = version

    def get_active_version(self, code: str) -> Optional[str]:
        """Return the version string currently set as active for the given template code."""
        with self._lock:
            return self._active_versions.get(code.lower())

    def remove(self, code: str, version: Optional[str] = None) -> None:
        """Remove one or all registered versions of a template code."""
        code_key = code.lower()
        with self._lock:
            if version is not None:
                key = (code_key, version)
                if key not in self._templates:
                    raise TemplateNotFoundException(f"Cannot remove: template '{code}' version '{version}' not registered.")
                del self._templates[key]
                if self._active_versions.get(code_key) == version:
                    # Promote another version if available
                    remaining = [v for (c, v) in self._templates.keys() if c == code_key]
                    if remaining:
                        self._active_versions[code_key] = sorted(remaining)[-1]
                    else:
                        self._active_versions.pop(code_key, None)
            else:
                # Remove all versions of this code
                keys_to_delete = [k for k in self._templates.keys() if k[0] == code_key]
                if not keys_to_delete:
                    raise TemplateNotFoundException(f"Cannot remove: no templates registered under code '{code}'.")
                for k in keys_to_delete:
                    del self._templates[k]
                self._active_versions.pop(code_key, None)
