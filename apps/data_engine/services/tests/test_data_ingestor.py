# apps/data_engine/services/tests/test_data_ingestor.py
"""Tests for DataIngestor service.

The suite validates:
- MAC_ENABLED flag handling
- tenant_id validation
- connector registration/retrieval
- successful ingestion returns a proper MacContext
"""

import os
import importlib
import pytest

from apps.data_engine.services.data_ingestor import DataIngestor
from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.core.exceptions import MacError, ComponentNotFoundError
from apps.data_engine.components.base import BaseComponent, MacContext

# Helper dummy connector
class DummyConnector(BaseComponent):
    component_type = "connector"

    def execute(self, context: MacContext):  # type: ignore[override]
        return {"payload": {"dummy": "value"}, "metadata": {"processed": True}}

@pytest.fixture(autouse=True)
def reset_registry(monkeypatch):
    # Clean registry before each test
    registry = MacRegistry.global_registry()
    registry._components.clear()
    yield
    registry._components.clear()

def _reload_settings(monkeypatch, enabled: str):
    monkeypatch.setenv("MAC_ENABLED", enabled)
    import backend.config.mac_settings as cfg
    importlib.reload(cfg)

def test_mac_disabled_raises(monkeypatch):
    _reload_settings(monkeypatch, "false")
    ingestor = DataIngestor()
    with pytest.raises(MacError, match="MAC está desactivado"):
        ingestor.ingest("dummy", None, "t1", "r1", "u1")

def test_empty_tenant_id_raises(monkeypatch):
    _reload_settings(monkeypatch, "true")
    ingestor = DataIngestor()
    with pytest.raises(MacError, match="tenant_id es obligatorio"):
        ingestor.ingest("dummy", None, "", "r1", "u1")

def test_missing_connector_raises(monkeypatch):
    _reload_settings(monkeypatch, "true")
    ingestor = DataIngestor()
    with pytest.raises(ComponentNotFoundError):
        ingestor.ingest("nonexistent", None, "t1", "r1", "u1")

def test_successful_ingest(monkeypatch):
    _reload_settings(monkeypatch, "true")
    registry = MacRegistry.global_registry()
    registry.register("dummy", DummyConnector())
    ingestor = DataIngestor()
    ctx = ingestor.ingest("dummy", "src", "t1", "r1", "u1")
    assert isinstance(ctx, dict)
    assert ctx["tenant_id"] == "t1"
    assert ctx["run_id"] == "r1"
    assert ctx["user_id"] == "u1"
    # payload from dummy connector
    assert ctx["payload"] == {"dummy": "value"}
    # source stored in metadata
    assert ctx["metadata"]["source"] == "src"
    # dummy connector added its own metadata element
    assert ctx["metadata"]["processed"] is True
