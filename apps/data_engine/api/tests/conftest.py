# apps/data_engine/api/tests/conftest.py
"""Fixtures for MAC REST API Gateway tests (TAREA 23)."""

import os
import sys
import pytest
import django
from django.conf import settings

# Ensure project root and `backend/` directory are in sys.path so Django can find `core`, `users`, etc.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
backend_dir = os.path.join(project_root, "backend")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
django.setup()

# Configure SQLite memory DB and filter out PostgreSQL RLS middlewares for isolated API unit testing
settings.DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
settings.MIDDLEWARE = [
    m for m in settings.MIDDLEWARE
    if "TenantMiddleware" not in m and "JwtBootstrapMiddleware" not in m
]

from rest_framework.test import APIClient

from apps.data_engine.application.registry import ApplicationServiceRegistry
from apps.data_engine.application.services import _RUN_TO_SESSION, _SESSION_STORE
from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.events.registry import EventBusRegistry
from apps.data_engine.progress.registry import ProgressRegistry


@pytest.fixture(autouse=True)
def reset_registries_stores_and_drf_settings():
    """Clean all registries and session stores before and after every test."""
    ApplicationServiceRegistry.global_registry().clear()
    MacRegistry.global_registry()._components.clear()
    EventBusRegistry.global_registry().reset()
    ProgressRegistry.global_registry().clear()
    _SESSION_STORE.clear()
    _RUN_TO_SESSION.clear()

    # Ensure DRF exception handler points to our custom handler
    if not hasattr(settings, "REST_FRAMEWORK"):
        settings.REST_FRAMEWORK = {}
    settings.REST_FRAMEWORK["EXCEPTION_HANDLER"] = "apps.data_engine.api.exceptions.custom_mac_exception_handler"

    yield

    ApplicationServiceRegistry.global_registry().clear()
    MacRegistry.global_registry()._components.clear()
    EventBusRegistry.global_registry().reset()
    ProgressRegistry.global_registry().clear()
    _SESSION_STORE.clear()
    _RUN_TO_SESSION.clear()


@pytest.fixture
def api_client():
    return APIClient()
