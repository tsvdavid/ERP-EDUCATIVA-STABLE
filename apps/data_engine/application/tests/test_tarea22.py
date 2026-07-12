# apps/data_engine/application/tests/test_tarea22.py
"""Comprehensive certification test suite for TAREA 22.

Covers:
1. Abstract contracts and immutable DTOs (`frozen=True`).
2. Exception hierarchy and inheritance (`MacError`).
3. Thread-safe `ApplicationServiceRegistry` and dynamic resolution.
4. Concrete application services (`ImportService`, `ValidationService`, `PreviewService`,
   `ExportService`, `ProgressService`, `SessionService`, `EventService`).
5. `MacApplicationFacade` verifying all 9 public entry point methods.
6. Cross-layer integration with `ImportWorkflowOrchestrator`, `ProgressTracker` (TAREA 20),
   and `EventBusBridgeObserver` (TAREA 21).
7. Zero-ORM enforcement across the entire `application/` package.
"""

import ast
import os
from dataclasses import FrozenInstanceError
from typing import Any, Dict

import pytest

from apps.data_engine.application.base import ApplicationContext
from apps.data_engine.application.contracts import (
    BaseApplicationService,
    BaseEventService,
    BaseExportService,
    BaseImportService,
    BasePreviewService,
    BaseProgressService,
    BaseSessionService,
    BaseValidationService,
)
from apps.data_engine.application.dto import (
    ErrorExportResponse,
    EventListResponse,
    ImportRequest,
    ImportResponse,
    PreviewResponse,
    ProgressResponse,
    SessionResponse,
    ValidationRequest,
    ValidationResponse,
)
from apps.data_engine.application.exceptions import (
    ApplicationException,
    ImportException,
    ServiceUnavailableException,
    SessionException,
    ValidationException,
)
from apps.data_engine.application.facade import MacApplicationFacade
from apps.data_engine.application.registry import ApplicationServiceRegistry
from apps.data_engine.application.services import (
    EventService,
    ExportService,
    ImportService,
    PreviewService,
    ProgressService,
    SessionService,
    ValidationService,
)
from apps.data_engine.components.base import BaseComponent
from apps.data_engine.core.exceptions import MacError
from apps.data_engine.core.registry import MacRegistry


# ===========================================================================
# Mock Components for Workflow Testing
# ===========================================================================
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


class MockValidator(BaseComponent):
    def get_name(self) -> str:
        return "mock_validator"

    def execute(self, context: Dict[str, Any]) -> Any:
        # Check rule violation simulation if specific source value passed
        source = context.get("source")
        if source == "invalid_source":
            return {"errors": ["Rule 'mock_validator' violated: missing required header"]}
        return {"errors": []}


# ===========================================================================
# 1. Abstract Contracts & DTO Immutability Tests
# ===========================================================================
class TestContractsAndDTOs:
    def test_abstract_contracts_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            BaseImportService()  # type: ignore[abstract]
        with pytest.raises(TypeError):
            BaseValidationService()  # type: ignore[abstract]

    def test_dto_immutability_enforced(self):
        req = ImportRequest(
            tenant_id="tenant_x",
            user_id="user_y",
            source="file.csv",
            pipeline_config={"reader": ["mock_reader"]},
        )
        with pytest.raises(FrozenInstanceError):
            req.tenant_id = "tenant_z"  # type: ignore[misc]

        res = ImportResponse(
            session_id="s1",
            run_id="r1",
            state="COMPLETED",
            total_records=10,
            processed_records=10,
            errors=[],
        )
        with pytest.raises(FrozenInstanceError):
            res.state = "FAILED"  # type: ignore[misc]

    def test_dto_to_dict_serialization(self):
        req = ImportRequest(
            tenant_id="t1",
            user_id="u1",
            source="test.csv",
            pipeline_config={"parser": ["mock_parser"]},
        )
        d = req.to_dict()
        assert d["tenant_id"] == "t1"
        assert d["pipeline_config"]["parser"] == ["mock_parser"]

        val_res = ValidationResponse(is_valid=False, total_checked=2, violations=[{"rule": "r1", "error": "err"}])
        assert val_res.to_dict()["violations"][0]["error"] == "err"


# ===========================================================================
# 2. Exceptions Hierarchy Tests
# ===========================================================================
class TestApplicationExceptions:
    def test_exception_hierarchy(self):
        assert issubclass(ApplicationException, MacError)
        assert issubclass(ValidationException, ApplicationException)
        assert issubclass(SessionException, ApplicationException)
        assert issubclass(ImportException, ApplicationException)
        assert issubclass(ServiceUnavailableException, ApplicationException)


# ===========================================================================
# 3. ApplicationServiceRegistry Tests
# ===========================================================================
class TestApplicationServiceRegistry:
    def test_singleton_and_defaults_registration(self):
        reg = ApplicationServiceRegistry.global_registry()
        assert reg.get("import") is not None
        assert isinstance(reg.get("import"), BaseImportService)
        assert isinstance(reg.get_service(BaseValidationService), BaseValidationService)

    def test_custom_service_registration_and_resolution(self):
        reg = ApplicationServiceRegistry.global_registry()
        custom_import = ImportService()
        reg.register("custom_imp", custom_import)
        assert reg.get("custom_imp") is custom_import

    def test_missing_service_raises_unavailable(self):
        reg = ApplicationServiceRegistry.global_registry()
        with pytest.raises(ServiceUnavailableException):
            reg.get("non_existent_service")


# ===========================================================================
# 4. Concrete Services Tests
# ===========================================================================
class TestConcreteServices:
    def test_preview_service_with_list_dict_and_string(self):
        preview_srv = PreviewService()
        # List of dicts
        res = preview_srv.preview([{"name": "Alice", "score": 95}, {"name": "Bob", "score": 88}], limit=1)
        assert res.total_preview_records == 1
        assert res.headers == ["name", "score"]
        assert res.sample_rows[0]["name"] == "Alice"

        # Dict
        res_dict = preview_srv.preview({"col1": "v1", "col2": "v2"})
        assert res_dict.headers == ["col1", "col2"]
        assert res_dict.sample_rows[0]["col1"] == "v1"

    def test_validation_service_detects_violations(self):
        MacRegistry.global_registry().register("mock_validator", MockValidator())
        val_srv = ValidationService()

        # Valid execution
        req_valid = ValidationRequest(tenant_id="t1", source="valid.csv", rules=["mock_validator"])
        res_valid = val_srv.validate(req_valid)
        assert res_valid.is_valid is True
        assert res_valid.total_checked == 1
        assert len(res_valid.violations) == 0

        # Invalid execution triggering violation
        req_invalid = ValidationRequest(tenant_id="t1", source="invalid_source", rules=["mock_validator"])
        res_invalid = val_srv.validate(req_invalid)
        assert res_invalid.is_valid is False
        assert len(res_invalid.violations) == 1
        assert "violated" in res_invalid.violations[0]["error"]

    def test_import_service_workflow_execution_and_stores(self):
        MacRegistry.global_registry().register("mock_reader", MockReader())
        MacRegistry.global_registry().register("mock_parser", MockParser())
        imp_srv = ImportService()

        req = ImportRequest(
            tenant_id="tenant_acme",
            user_id="user_admin",
            source="acme_data.csv",
            pipeline_config={
                "reader": ["mock_reader"],
                "parser": ["mock_parser"],
            },
        )
        res = imp_srv.start_import(req)
        assert res.session_id is not None
        assert res.run_id is not None
        assert res.is_success is True
        assert res.processed_records == 3

        # Test resume & cancel
        res_resumed = imp_srv.resume(res.session_id)
        assert res_resumed.state == "RESUMED"

        res_cancelled = imp_srv.cancel(res.session_id)
        assert res_cancelled.state == "ABORTED"
        assert res_cancelled.is_success is False


# ===========================================================================
# 5. MacApplicationFacade 9 Entry Points Test
# ===========================================================================
class TestMacApplicationFacade:
    def test_facade_exposes_all_nine_public_methods(self):
        MacRegistry.global_registry().register("mock_reader", MockReader())
        MacRegistry.global_registry().register("mock_parser", MockParser())
        facade = MacApplicationFacade()

        # 1. start_import
        req = ImportRequest(
            tenant_id="tenant_facade",
            user_id="user_facade",
            source="data.csv",
            pipeline_config={"reader": ["mock_reader"], "parser": ["mock_parser"]},
        )
        imp_res = facade.start_import(req)
        assert imp_res.is_success is True
        session_id = imp_res.session_id

        # 2. validate
        val_res = facade.validate(ValidationRequest(tenant_id="t1", source="data.csv", rules=[]))
        assert val_res.is_valid is True

        # 3. preview
        prev_res = facade.preview([{"id": 100, "item": "Box"}])
        assert prev_res.headers == ["id", "item"]

        # 4. get_progress
        prog_res = facade.get_progress(session_id)
        assert prog_res.session_id == session_id
        assert prog_res.processed == 3

        # 5. get_session
        sess_res = facade.get_session(session_id)
        assert sess_res.tenant_id == "tenant_facade"
        assert len(sess_res.phases) >= 2

        # 6. get_events
        ev_res = facade.get_events(session_id)
        assert ev_res.session_id == session_id
        assert len(ev_res.events) >= 1  # Should contain at least SESSION_START / progress events

        # 7. export_errors
        err_res = facade.export_errors(session_id, format_type="json")
        assert err_res.export_format == "json"
        assert err_res.error_count == 0

        # 8. resume
        resumed = facade.resume(session_id)
        assert resumed.state == "RESUMED"

        # 9. cancel
        cancelled = facade.cancel(session_id)
        assert cancelled.state == "ABORTED"


# ===========================================================================
# 6. Cross-Layer Integration (Orchestrator + Progress + EventBus)
# ===========================================================================
class TestCrossLayerIntegration:
    def test_import_auto_connects_progress_tracker_to_event_bus(self):
        MacRegistry.global_registry().register("mock_reader", MockReader())
        MacRegistry.global_registry().register("mock_parser", MockParser())
        facade = MacApplicationFacade()

        req = ImportRequest(
            tenant_id="tenant_events",
            user_id="user_events",
            source="stream.csv",
            pipeline_config={"reader": ["mock_reader"], "parser": ["mock_parser"]},
        )
        res = facade.start_import(req)

        # Verify that progress tracker received events
        progress = facade.get_progress(res.session_id)
        assert progress.processed == 3

        # Verify that those progress events flowed across EventBusBridgeObserver to EventDispatcher
        event_list = facade.get_events(res.session_id)
        assert len(event_list.events) > 0

        event_types = [e["event_type"] for e in event_list.events]
        assert "SESSION_START" in event_types
        assert "SESSION_END" in event_types or "PHASE_PROGRESS" in event_types


# ===========================================================================
# 7. Zero-ORM Enforcement Audit
# ===========================================================================
class TestZeroOrmEnforcement:
    def test_application_layer_has_no_django_orm_dependencies(self):
        """Forensic inspection guaranteeing no ORM imports exist in application/."""
        app_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
        forbidden_terms = ["django.db", "models.Model", "transaction.atomic", "QuerySet"]

        for root, _, files in os.walk(app_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    for term in forbidden_terms:
                        assert term not in content, (
                            f"Zero-ORM violation: found '{term}' in {os.path.relpath(filepath, app_dir)}"
                        )

                    # Also verify via AST that no `import django.db` occurs
                    tree = ast.parse(content, filename=filepath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                assert not alias.name.startswith("django.db"), (
                                    f"Forbidden import '{alias.name}' in {filepath}"
                                )
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                assert not node.module.startswith("django.db"), (
                                    f"Forbidden from-import '{node.module}' in {filepath}"
                                )
