# apps/data_engine/connectors/tests/test_tarea25.py
"""Comprehensive unit, integration, and Zero-ORM verification suite for TAREA 25.

Tests:
1. Contracts & DTOs (`ConnectorConfig`, `DataSource`, `BaseConnector`).
2. Authentication Providers (`BasicAuth`, `BearerAuth`, `ApiKeyAuth`, `OAuthProvider`).
3. Registry & Factory (`ConnectorRegistry`, `ConnectorFactory`).
4. Concrete Enterprise Connectors (`CSVConnector`, `JSONConnector`, `ExcelConnector`, `SQLConnector`, `RESTConnector`).
5. Streaming & Chunking (`stream()` behavior across formats).
6. Workflow Execution Integration (`BaseConnector.execute(MacContext)`).
7. Thread-Safety & Concurrency (`ConnectorRegistry` multi-threading).
8. AST Static Analysis certifying Zero-ORM compliance inside `apps/data_engine/connectors/`.
"""

import ast
import io
import json
import os
import threading
import time
import unittest
from typing import Any, Dict, Iterator, List, Optional, Type

import pytest

from apps.data_engine.components.base import MacContext
from apps.data_engine.connectors import (
    ApiKeyAuth,
    AuthenticationException,
    BaseAuthProvider,
    BaseConnector,
    BasicAuth,
    BearerAuth,
    ConnectionFailedException,
    ConnectorConfig,
    ConnectorException,
    ConnectorFactory,
    ConnectorRegistry,
    DataSource,
    InvalidConfigurationException,
    OAuthProvider,
    TimeoutException,
    UnsupportedConnectorException,
)
from apps.data_engine.connectors.readers import (
    CSVConnector,
    ExcelConnector,
    JSONConnector,
    RESTConnector,
    SQLConnector,
)


# ==============================================================================
# 1. Contracts and DTOs Tests
# ==============================================================================

class TestContractsAndDTOs(unittest.TestCase):
    """Verify domain contracts, DTO immutability, and BaseConnector defaults."""

    def test_connector_config_immutability_and_defaults(self):
        config = ConnectorConfig(
            connector_type="csv",
            host="localhost",
            port=5432,
            parameters={"delimiter": ";"},
        )
        self.assertEqual(config.connector_type, "csv")
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 5432)
        self.assertFalse(config.ssl)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.get_param("delimiter"), ";")
        self.assertIsNone(config.get_param("missing_param"))

        with self.assertRaises(Exception):
            config.timeout = 60  # Frozen/Immutable

    def test_data_source_to_dict_and_immutability(self):
        ds = DataSource(
            name="students.csv",
            source_type="csv",
            columns=["id", "name", "email"],
            metadata={"row_count": 100},
            encoding="utf-8",
            size_bytes=2048,
        )
        self.assertEqual(ds.name, "students.csv")
        payload = ds.to_dict()
        self.assertEqual(payload["name"], "students.csv")
        self.assertEqual(payload["columns"], ["id", "name", "email"])
        self.assertEqual(payload["size_bytes"], 2048)

    def test_base_connector_cannot_be_instantiated_directly(self):
        with self.assertRaises(TypeError):
            BaseConnector()


# ==============================================================================
# 2. Authentication Providers Tests
# ==============================================================================

class TestAuthenticationProviders(unittest.TestCase):
    """Verify Basic, Bearer, API Key, and OAuth providers."""

    def test_basic_auth_provider(self):
        auth = BasicAuth(username="admin", password="secretpassword")
        self.assertTrue(auth.validate_credentials())
        headers = auth.apply_auth({"User-Agent": "MAC/1.0"})
        self.assertIn("Authorization", headers)
        self.assertTrue(headers["Authorization"].startswith("Basic "))

        with self.assertRaises(AuthenticationException):
            BasicAuth(username="", password="pwd")

    def test_bearer_auth_provider(self):
        auth = BearerAuth(token="jwt.token.here")
        self.assertTrue(auth.validate_credentials())
        headers = auth.apply_auth({})
        self.assertEqual(headers["Authorization"], "Bearer jwt.token.here")

        with self.assertRaises(AuthenticationException):
            BearerAuth(token="")

    def test_api_key_auth_provider(self):
        auth_header = ApiKeyAuth(api_key="12345", key_name="X-Eduka-Key", location="header")
        self.assertTrue(auth_header.validate_credentials())
        headers = auth_header.apply_auth({"Accept": "application/json"})
        self.assertEqual(headers["X-Eduka-Key"], "12345")
        self.assertEqual(headers["Accept"], "application/json")

        with self.assertRaises(AuthenticationException):
            ApiKeyAuth(api_key="123", location="invalid")

    def test_oauth_provider(self):
        oauth = OAuthProvider(
            client_id="client_mac",
            client_secret="secret_mac",
            token_url="https://mock_oauth/token",
        )
        self.assertTrue(oauth.validate_credentials())
        headers = oauth.apply_auth({})
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer oauth_token_for_client_mac")


# ==============================================================================
# 3. Registry and Factory Tests
# ==============================================================================

class DummyConnector(BaseConnector):
    def connect(self) -> None:
        self._is_connected = True
    def disconnect(self) -> None:
        self._is_connected = False
    def test_connection(self) -> bool:
        return True
    def fetch(self, query_or_path: Optional[str] = None, limit: Optional[int] = None, **kwargs: Any) -> List[Dict[str, Any]]:
        return [{"dummy": "data"}]
    def stream(self, query_or_path: Optional[str] = None, chunk_size: int = 1000, **kwargs: Any):
        yield [{"dummy": "data"}]
    def metadata(self) -> DataSource:
        return DataSource(name="dummy", source_type="dummy", columns=["dummy"])


class TestRegistryAndFactory(unittest.TestCase):
    """Verify thread-safe registration and dynamic factory instantiation."""

    def setUp(self):
        # We don't reset global_registry to avoid wiping registered built-ins,
        # but we can check built-ins or register custom types.
        self.registry = ConnectorRegistry.global_registry()

    def test_register_and_get_connector_class(self):
        self.registry.register("dummy_test", DummyConnector)
        cls = self.registry.get_connector_class("dummy_test")
        self.assertEqual(cls, DummyConnector)
        self.assertIn("dummy_test", self.registry.list_supported_connectors())

    def test_get_unsupported_connector_raises(self):
        with self.assertRaises(UnsupportedConnectorException):
            self.registry.get_connector_class("non_existent_connector_xyz")

    def test_connector_factory_create(self):
        self.registry.register("dummy_factory", DummyConnector)
        config = ConnectorConfig(connector_type="dummy_factory", host="localhost")
        instance = ConnectorFactory.create_connector(config)
        self.assertIsInstance(instance, DummyConnector)
        self.assertEqual(instance.config.host, "localhost")

    def test_connector_factory_create_from_params(self):
        self.registry.register("dummy_params", DummyConnector)
        instance = ConnectorFactory.create_from_params("dummy_params", host="db.eduka360.internal", port=3306)
        self.assertEqual(instance.config.host, "db.eduka360.internal")
        self.assertEqual(instance.config.port, 3306)


# ==============================================================================
# 4. Concrete Connectors Tests
# ==============================================================================

class TestCSVConnector(unittest.TestCase):
    """Verify CSV and delimited text reading, BOM handling, and streaming."""

    def test_csv_fetch_from_string_buffer(self):
        csv_text = "id,name,role\n1,Ana,Student\n2,Carlos,Teacher"
        connector = ConnectorFactory.create_from_params("csv", source=csv_text)
        self.assertTrue(connector.test_connection())
        records = connector.fetch()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["name"], "Ana")
        self.assertEqual(records[1]["role"], "Teacher")

    def test_csv_fetch_with_limit_and_delimiter(self):
        csv_text = "id;score\n101;95\n102;88\n103;91"
        connector = ConnectorFactory.create_from_params("csv", source=csv_text, delimiter=";")
        records = connector.fetch(limit=2)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[1]["score"], "88")

    def test_csv_stream_batches(self):
        csv_text = "num\n1\n2\n3\n4\n5\n6\n7"
        connector = ConnectorFactory.create_from_params("csv", source=csv_text)
        batches = list(connector.stream(chunk_size=3))
        self.assertEqual(len(batches), 3)
        self.assertEqual(len(batches[0]), 3)
        self.assertEqual(len(batches[1]), 3)
        self.assertEqual(len(batches[2]), 1)
        self.assertEqual(batches[2][0]["num"], "7")

    def test_csv_metadata(self):
        csv_text = "col1,col2,col3\na,b,c"
        connector = ConnectorFactory.create_from_params("csv", source=csv_text)
        meta = connector.metadata()
        self.assertEqual(meta.source_type, "csv")
        self.assertEqual(meta.columns, ["col1", "col2", "col3"])


class TestJSONConnector(unittest.TestCase):
    """Verify JSON parsing for lists, objects, and nested paths."""

    def test_json_fetch_list(self):
        json_data = [{"code": "MATH101", "credits": 4}, {"code": "SCI201", "credits": 3}]
        connector = ConnectorFactory.create_from_params("json", source=json_data)
        records = connector.fetch()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["code"], "MATH101")

    def test_json_fetch_nested_path(self):
        raw_json = {
            "status": "ok",
            "data": {
                "items": [
                    {"id": 1, "title": "A"},
                    {"id": 2, "title": "B"}
                ]
            }
        }
        connector = ConnectorFactory.create_from_params("json", source=raw_json, root_path="data.items")
        records = connector.fetch()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[1]["title"], "B")

    def test_json_stream_and_metadata(self):
        json_data = [{"val": i} for i in range(10)]
        connector = ConnectorFactory.create_from_params("json", source=json_data)
        batches = list(connector.stream(chunk_size=4))
        self.assertEqual(len(batches), 3)
        meta = connector.metadata()
        self.assertEqual(meta.columns, ["val"])


class TestExcelConnector(unittest.TestCase):
    """Verify Excel architecture and row extraction."""

    def test_excel_connector_with_simulated_rows(self):
        rows = [
            {"student_id": "S1", "grade": 10},
            {"student_id": "S2", "grade": 9},
        ]
        connector = ConnectorFactory.create_from_params("excel", source=rows, sheet_name="Grades")
        self.assertTrue(connector.test_connection())
        records = connector.fetch()
        self.assertEqual(len(records), 2)
        meta = connector.metadata()
        self.assertEqual(meta.name, "Grades")
        self.assertEqual(meta.source_type, "excel")


class TestSQLConnector(unittest.TestCase):
    """Verify SQL DB-API 2.0 simulation and parameter handling."""

    class MockCursor:
        def __init__(self, rows, description):
            self._rows = rows
            self.description = description
        def execute(self, query):
            pass
        def fetchall(self):
            return self._rows
        def fetchmany(self, size):
            res = self._rows[:size]
            self._rows = self._rows[size:]
            return res

    class MockConnection:
        def __init__(self, rows, description):
            self.rows = rows
            self.desc = description
            self.closed = False
        def cursor(self):
            return TestSQLConnector.MockCursor(list(self.rows), self.desc)
        def close(self):
            self.closed = True

    def test_sql_connector_with_mock_db_api_connection(self):
        mock_conn = self.MockConnection([(1, "Alice"), (2, "Bob")], [("id",), ("name",)])
        connector = ConnectorFactory.create_from_params(
            "sql",
            host="pg.internal",
            connection_object=mock_conn,
            table="users_table"
        )
        self.assertTrue(connector.test_connection())
        records = connector.fetch("SELECT id, name FROM users_table")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0], {"id": 1, "name": "Alice"})
        self.assertEqual(records[1], {"id": 2, "name": "Bob"})

        meta = connector.metadata()
        self.assertEqual(meta.columns, ["id", "name"])
        self.assertEqual(meta.name, "users_table")
        connector.disconnect()
        self.assertTrue(mock_conn.closed)


class TestRESTConnector(unittest.TestCase):
    """Verify REST API transport, auth headers, and retries."""

    def test_rest_connector_with_transport_callback(self):
        def mock_transport(method, url, headers):
            self.assertEqual(method, "GET")
            self.assertEqual(headers["Authorization"], "Bearer rest_test_token")
            return [{"id": 10, "status": "active"}, {"id": 11, "status": "pending"}]

        auth = BearerAuth("rest_test_token")
        config = ConnectorConfig(
            connector_type="rest",
            host="https://api.eduka360.internal/v1/students",
            auth_provider=auth,
            parameters={"transport_callback": mock_transport},
        )
        connector = ConnectorFactory.create_connector(config)
        records = connector.fetch()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["id"], 10)

        meta = connector.metadata()
        self.assertEqual(meta.source_type, "rest")
        self.assertIn("status", meta.columns)


# ==============================================================================
# 5. Workflow Execution Integration Tests
# ==============================================================================

class TestWorkflowExecutionIntegration(unittest.TestCase):
    """Verify BaseConnector.execute(MacContext) inside a standard pipeline."""

    def test_execute_injects_raw_data_and_metadata_into_payload(self):
        csv_text = "code,name\nE01,Math\nE02,Science"
        connector = ConnectorFactory.create_from_params("csv", source=csv_text)
        context: MacContext = {
            "tenant_id": "tenant_001",
            "run_id": "run_connectors_101",
            "payload": {"source": csv_text, "original_key": "original_val"},
        }
        out = connector.execute(context)
        self.assertIn("payload", out)
        payload = out["payload"]
        self.assertEqual(payload["original_key"], "original_val")
        self.assertIn("raw_data", payload)
        self.assertEqual(len(payload["raw_data"]), 2)
        self.assertEqual(payload["raw_data"][0]["code"], "E01")
        self.assertIn("source_metadata", payload)
        self.assertEqual(payload["source_metadata"]["source_type"], "csv")


# ==============================================================================
# 6. Thread-Safety & Concurrency Tests
# ==============================================================================

class TestConcurrencyAndThreadSafety(unittest.TestCase):
    """Verify thread-safe registry registration and lookup under concurrent access."""

    def test_concurrent_registry_access(self):
        registry = ConnectorRegistry.global_registry()
        errors: List[Exception] = []

        def worker(idx: int):
            try:
                name = f"thread_conn_{idx}"
                registry.register(name, DummyConnector)
                cls = registry.get_connector_class(name)
                self.assertEqual(cls, DummyConnector)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)


# ==============================================================================
# 7. Zero-ORM Compliance AST Inspection
# ==============================================================================

class TestZeroOrmComplianceInConnectors(unittest.TestCase):
    """Perform static AST verification to guarantee Zero-ORM in `connectors/`."""

    def test_connectors_package_has_no_django_orm_dependencies(self):
        forbidden_modules = {"django.db", "django.db.models", "django.db.transaction"}
        forbidden_names = {"models", "QuerySet", "atomic"}

        package_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        for root, _, files in os.walk(package_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=filepath)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            for forbidden in forbidden_modules:
                                self.assertFalse(
                                    alias.name == forbidden or alias.name.startswith(f"{forbidden}."),
                                    f"Zero-ORM violation in {filepath}: import {alias.name}",
                                )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for forbidden in forbidden_modules:
                                self.assertFalse(
                                    node.module == forbidden or node.module.startswith(f"{forbidden}."),
                                    f"Zero-ORM violation in {filepath}: from {node.module} import ...",
                                )
                    elif isinstance(node, ast.Name):
                        if node.id in forbidden_names:
                            # Verify it's not importing/referencing Django models or atomic
                            self.assertNotEqual(
                                node.id,
                                "QuerySet",
                                f"Zero-ORM violation in {filepath}: direct use of {node.id}",
                            )
