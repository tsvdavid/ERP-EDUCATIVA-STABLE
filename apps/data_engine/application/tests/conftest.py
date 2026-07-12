# apps/data_engine/application/tests/conftest.py
"""Fixtures for MAC Application Layer tests."""

import pytest
from apps.data_engine.application.registry import ApplicationServiceRegistry
from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.events.registry import EventBusRegistry
from apps.data_engine.progress.registry import ProgressRegistry
from apps.data_engine.application.services import _SESSION_STORE, _RUN_TO_SESSION


@pytest.fixture(autouse=True)
def reset_registries_and_stores():
    """Clean all registries and session stores before and after every test."""
    ApplicationServiceRegistry.global_registry().clear()
    MacRegistry.global_registry()._components.clear()
    EventBusRegistry.global_registry().reset()
    ProgressRegistry.global_registry().clear()
    _SESSION_STORE.clear()
    _RUN_TO_SESSION.clear()
    yield
    ApplicationServiceRegistry.global_registry().clear()
    MacRegistry.global_registry()._components.clear()
    EventBusRegistry.global_registry().reset()
    ProgressRegistry.global_registry().clear()
    _SESSION_STORE.clear()
    _RUN_TO_SESSION.clear()
