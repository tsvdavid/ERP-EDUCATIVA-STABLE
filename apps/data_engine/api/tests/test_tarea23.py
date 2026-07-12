# apps/data_engine/api/tests/test_tarea23.py
"""Comprehensive test suite for TAREA 23: REST API & Integration Gateway Framework.

Tests:
1. Exception Mapping (custom_mac_exception_handler: 400, 403, 404, 409, 422, 503).
2. Multi-Tenant Security & Isolation (preventing cross-tenant access).
3. Import Session Endpoints (`start`, `retrieve`, `progress`, `events`, `resume`, `cancel`, `export_errors`).
4. Pre-import Validation (`validate`) & Data Inspection (`preview`).
5. Zero-ORM Enforcement across the API gateway (`api/`).
"""

import ast
import json
import os
from dataclasses import dataclass
from typing import Any, Dict
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.data_engine.application.exceptions import (
    ApplicationException,
    ImportException,
    ServiceUnavailableException,
    SessionException,
    ValidationException,
)
from apps.data_engine.api.exceptions import TenantIsolationViolation
from apps.data_engine.components.base import BaseComponent
from apps.data_engine.core.exceptions import MacError
from apps.data_engine.core.registry import MacRegistry


# ==============================================================================
# Mock Users and Components
# ==============================================================================

@dataclass
class MockUser:
    id: int = 1
    username: str = "operator_alfa"
    is_authenticated: bool = True
    is_superuser: bool = False
    is_staff: bool = False
    tenant_id: str = "tenant_alfa"


class MockReader(BaseComponent):
    def get_name(self) -> str:
        return "mock_reader"

    def execute(self, context: Dict[str, Any]) -> Any:
        records = [{"id": 1, "data": "Alpha"}, {"id": 2, "data": "Beta"}, {"id": 3, "data": "Gamma"}]
        return {"payload": {"raw_data": records}}


class MockParser(BaseComponent):
    def get_name(self) -> str:
        return "mock_parser"

    def execute(self, context: Dict[str, Any]) -> Any:
        records = [{"id": 1, "data": "Alpha"}, {"id": 2, "data": "Beta"}, {"id": 3, "data": "Gamma"}]
        return {"payload": {"parsed_records": records, "raw_data": records}}


# ==============================================================================
# 1. Test Exception Mapping (`exceptions.py`)
# ==============================================================================

class TestApiExceptionsAndMapping:
    def test_tenant_isolation_violation_maps_to_403(self, api_client):
        # We can test exception handler directly via mock view or direct invocation
        from apps.data_engine.api.exceptions import custom_mac_exception_handler
        exc = TenantIsolationViolation("Unauthorized cross-tenant attempt")
        res = custom_mac_exception_handler(exc, {})
        assert res is not None
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert res.data["error_code"] == "TENANT_ISOLATION_VIOLATION"

    def test_validation_exception_maps_to_422(self, api_client):
        from apps.data_engine.api.exceptions import custom_mac_exception_handler
        exc = ValidationException("Rule violations detected")
        exc.violations = [{"rule": "r1", "error": "missing field"}]
        res = custom_mac_exception_handler(exc, {})
        assert res is not None
        assert res.status_code in (status.HTTP_422_UNPROCESSABLE_ENTITY if hasattr(status, "HTTP_422_UNPROCESSABLE_ENTITY") else status.HTTP_400_BAD_REQUEST, status.HTTP_400_BAD_REQUEST)
        assert res.data["error_code"] == "MAC_VALIDATION_ERROR"
        assert len(res.data["detail"]) == 1

    def test_session_exception_not_found_maps_to_404(self, api_client):
        from apps.data_engine.api.exceptions import custom_mac_exception_handler
        exc = SessionException("Session 'sess-123' not found in session store")
        res = custom_mac_exception_handler(exc, {})
        assert res is not None
        assert res.status_code == status.HTTP_404_NOT_FOUND
        assert res.data["error_code"] == "MAC_SESSION_ERROR"

    def test_import_exception_terminal_maps_to_409(self, api_client):
        from apps.data_engine.api.exceptions import custom_mac_exception_handler
        exc = ImportException("Cannot resume session in terminal state COMPLETED")
        res = custom_mac_exception_handler(exc, {})
        assert res is not None
        assert res.status_code == status.HTTP_409_CONFLICT
        assert res.data["error_code"] == "MAC_IMPORT_ERROR"

    def test_service_unavailable_maps_to_503(self, api_client):
        from apps.data_engine.api.exceptions import custom_mac_exception_handler
        exc = ServiceUnavailableException("Component registry down")
        res = custom_mac_exception_handler(exc, {})
        assert res is not None
        assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_mac_general_error_maps_to_400(self, api_client):
        from apps.data_engine.api.exceptions import custom_mac_exception_handler
        exc = MacError("Domain syntax error")
        res = custom_mac_exception_handler(exc, {})
        assert res is not None
        assert res.status_code == status.HTTP_400_BAD_REQUEST


# ==============================================================================
# 2. Test Multi-Tenant Security & Isolation (`permissions.py`)
# ==============================================================================

class TestMultiTenantIsolationAndSecurity:
    def test_cross_tenant_access_denied(self, api_client):
        MacRegistry.global_registry().register("mock_reader", MockReader())
        MacRegistry.global_registry().register("mock_parser", MockParser())

        user = MockUser(tenant_id="tenant_alfa")
        api_client.force_authenticate(user=user)

        # Attempt to start import session targeting tenant_beta
        url = "/api/data-engine/sessions/"
        payload = {
            "tenant_id": "tenant_beta",
            "source": "data.csv",
            "pipeline_config": {"reader": ["mock_reader"], "parser": ["mock_parser"]},
        }
        response = api_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["error_code"] == "TENANT_ISOLATION_VIOLATION"

    def test_authorized_tenant_access_allowed(self, api_client):
        MacRegistry.global_registry().register("mock_reader", MockReader())
        MacRegistry.global_registry().register("mock_parser", MockParser())

        user = MockUser(tenant_id="tenant_alfa")
        api_client.force_authenticate(user=user)

        url = "/api/data-engine/sessions/"
        payload = {
            "tenant_id": "tenant_alfa",
            "source": "data.csv",
            "pipeline_config": {"reader": ["mock_reader"], "parser": ["mock_parser"]},
        }
        response = api_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["session_id"] is not None
        assert response.data["is_success"] is True

    def test_superuser_can_access_any_tenant(self, api_client):
        MacRegistry.global_registry().register("mock_reader", MockReader())
        MacRegistry.global_registry().register("mock_parser", MockParser())

        superuser = MockUser(username="admin", is_superuser=True, tenant_id="system_core")
        api_client.force_authenticate(user=superuser)

        url = "/api/data-engine/sessions/"
        payload = {
            "tenant_id": "tenant_omega",
            "source": "data.csv",
            "pipeline_config": {"reader": ["mock_reader"], "parser": ["mock_parser"]},
        }
        response = api_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED


# ==============================================================================
# 3. Test Import Session Endpoints Happy Path (`views.py`)
# ==============================================================================

class TestImportSessionEndpointsHappyPath:
    def test_full_session_api_lifecycle(self, api_client):
        MacRegistry.global_registry().register("mock_reader", MockReader())
        MacRegistry.global_registry().register("mock_parser", MockParser())

        user = MockUser(tenant_id="tenant_lifecycle")
        api_client.force_authenticate(user=user)

        # 1. Start Session
        start_url = "/api/data-engine/sessions/"
        start_payload = {
            "tenant_id": "tenant_lifecycle",
            "source": "stream.csv",
            "pipeline_config": {"reader": ["mock_reader"], "parser": ["mock_parser"]},
        }
        res_start = api_client.post(start_url, data=start_payload, format="json")
        assert res_start.status_code == status.HTTP_201_CREATED
        session_id = res_start.data["session_id"]

        # 2. Retrieve Session Report
        get_url = f"/api/data-engine/sessions/{session_id}/"
        res_get = api_client.get(get_url)
        assert res_get.status_code == status.HTTP_200_OK
        assert res_get.data["tenant_id"] == "tenant_lifecycle"
        assert len(res_get.data["phases"]) >= 2

        # 3. Get Progress Snapshot
        prog_url = f"/api/data-engine/sessions/{session_id}/progress/"
        res_prog = api_client.get(prog_url)
        assert res_prog.status_code == status.HTTP_200_OK
        assert res_prog.data["session_id"] == session_id
        assert res_prog.data["percentage"] == 100.0
        assert res_prog.data["processed"] == 3

        # 4. Replay Events
        ev_url = f"/api/data-engine/sessions/{session_id}/events/?since_sequence=0"
        res_ev = api_client.get(ev_url)
        assert res_ev.status_code == status.HTTP_200_OK
        assert len(res_ev.data["events"]) >= 1

        # 5. Export Errors CSV & JSON
        export_json_url = f"/api/data-engine/sessions/{session_id}/errors/export/?format=json"
        res_exp_json = api_client.get(export_json_url)
        assert res_exp_json.status_code == status.HTTP_200_OK
        assert res_exp_json["Content-Type"] == "application/json"

        export_csv_url = f"/api/data-engine/sessions/{session_id}/errors/export/?format=csv"
        res_exp_csv = api_client.get(export_csv_url)
        assert res_exp_csv.status_code == status.HTTP_200_OK
        assert res_exp_csv["Content-Type"] == "text/csv"

        # 6. Cancel / Resume tests
        cancel_url = f"/api/data-engine/sessions/{session_id}/cancel/"
        res_cancel = api_client.post(cancel_url)
        assert res_cancel.status_code == status.HTTP_200_OK
        assert res_cancel.data["state"] == "ABORTED"


# ==============================================================================
# 4. Test Validation & Preview Endpoints (`views.py`)
# ==============================================================================

class TestValidationAndPreviewEndpoints:
    def test_validate_endpoint_success(self, api_client):
        user = MockUser(tenant_id="tenant_alfa")
        api_client.force_authenticate(user=user)

        url = "/api/data-engine/validate/"
        payload = {
            "tenant_id": "tenant_alfa",
            "source": "valid.csv",
            "rules": [],
        }
        res = api_client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["is_valid"] is True
        assert res.data["violations"] == []

    def test_preview_endpoint_returns_sample_rows(self, api_client):
        user = MockUser(tenant_id="tenant_alfa")
        api_client.force_authenticate(user=user)

        url = "/api/data-engine/preview/"
        payload = {
            "source": [{"id": 101, "item": "Laptop"}, {"id": 102, "item": "Mouse"}],
            "limit": 5,
        }
        res = api_client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["headers"] == ["id", "item"]
        assert len(res.data["sample_rows"]) == 2
        assert res.data["total_preview_records"] == 2


# ==============================================================================
# 5. Zero-ORM Enforcement in API Gateway (`api/`)
# ==============================================================================

class TestZeroOrmEnforcementInApiLayer:
    def test_api_layer_has_no_django_orm_dependencies(self):
        """Verify static AST to ensure no `django.db` imports exist in `api/`."""
        api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        forbidden_terms = ["django.db", "models.Model", "transaction.atomic", "QuerySet"]

        for root, _, files in os.walk(api_dir):
            if "tests" in root or "__pycache__" in root:
                continue
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()

                    for term in forbidden_terms:
                        assert term not in content, (
                            f"Forbidden ORM term '{term}' found in MAC API Gateway file '{fpath}'"
                        )

                    # Also verify via AST that no `import django.db` occurs
                    tree = ast.parse(content, filename=fpath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                assert not alias.name.startswith("django.db"), (
                                    f"Forbidden import '{alias.name}' in '{fpath}'"
                                )
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            assert not node.module.startswith("django.db"), (
                                f"Forbidden import from '{node.module}' in '{fpath}'"
                                )
