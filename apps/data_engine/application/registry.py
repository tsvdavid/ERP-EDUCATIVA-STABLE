# apps/data_engine/application/registry.py
"""Dynamic Application Service Registry (TAREA 22).

Provides thread-safe registration and resolution of application services by
string name or by abstract service contract (`BaseApplicationService` subtype).
"""

import threading
from typing import Any, Dict, Optional, Type, TypeVar

from .contracts import BaseApplicationService
from .exceptions import ServiceUnavailableException

T = TypeVar("T", bound=BaseApplicationService)


class ApplicationServiceRegistry:
    """Thread-safe Singleton registry for MAC Application layer services."""

    _instance: Optional["ApplicationServiceRegistry"] = None
    _lock = threading.RLock()

    def __init__(self):
        self._services_by_name: Dict[str, BaseApplicationService] = {}
        self._services_by_type: Dict[Type[BaseApplicationService], BaseApplicationService] = {}
        self._defaults_registered = False

    @classmethod
    def global_registry(cls) -> "ApplicationServiceRegistry":
        """Return the global singleton instance, creating it thread-safely if needed."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def register(
        self,
        key: Any,
        service_instance: BaseApplicationService,
    ) -> None:
        """Register a concrete service instance under a string name and/or abstract contract type."""
        if not isinstance(service_instance, BaseApplicationService):
            raise TypeError(f"Service instance {service_instance!r} must implement BaseApplicationService")

        with self._lock:
            if isinstance(key, str):
                self._services_by_name[key.lower()] = service_instance
                # Auto-register by contract types if not already registered or if overriding
                for base_cls in type(service_instance).__mro__:
                    if (
                        issubclass(base_cls, BaseApplicationService)
                        and base_cls is not BaseApplicationService
                        and base_cls is not type(service_instance)
                    ):
                        self._services_by_type[base_cls] = service_instance
            elif isinstance(key, type) and issubclass(key, BaseApplicationService):
                self._services_by_type[key] = service_instance
            else:
                raise TypeError(f"Registration key must be a string name or BaseApplicationService subtype, got {key!r}")

    def get_service(self, service_type: Type[T]) -> T:
        """Resolve a service instance by its abstract base contract type."""
        with self._lock:
            self._ensure_defaults()
            service = self._services_by_type.get(service_type)
            if service is None:
                raise ServiceUnavailableException(
                    f"No application service registered for contract type '{service_type.__name__}'"
                )
            return service  # type: ignore[return-value]

    def get(self, name: str) -> BaseApplicationService:
        """Resolve a service instance by its registered string name."""
        with self._lock:
            self._ensure_defaults()
            service = self._services_by_name.get(name.lower())
            if service is None:
                raise ServiceUnavailableException(
                    f"No application service registered with name '{name}'"
                )
            return service

    def clear(self) -> None:
        """Clear all registered services and reset defaults state (useful for testing)."""
        with self._lock:
            self._services_by_name.clear()
            self._services_by_type.clear()
            self._defaults_registered = False

    def _ensure_defaults(self) -> None:
        """Lazy auto-registration of standard application services."""
        if self._defaults_registered:
            return
        self._defaults_registered = True
        # Lazy import inside method to avoid circular import during package initialization
        from .services import (
            EventService,
            ExportService,
            ImportService,
            PreviewService,
            ProgressService,
            SessionService,
            ValidationService,
        )

        self.register("import", ImportService())
        self.register("validation", ValidationService())
        self.register("preview", PreviewService())
        self.register("export", ExportService())
        self.register("progress", ProgressService())
        self.register("session", SessionService())
        self.register("event", EventService())
