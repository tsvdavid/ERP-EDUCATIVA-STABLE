# apps/data_engine/api/views.py
"""DRF Controllers (Views and ViewSets) for the MAC API Gateway.

Exposes RESTful endpoints for starting import sessions, monitoring progress,
replaying real-time events, pre-validating datasets, and exporting error reports.
Delegates 100% of underlying business and pipeline logic to `MacApplicationFacade`.
"""

from typing import Any
from django.http import HttpResponse
from rest_framework import permissions, renderers, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class CSVRenderer(renderers.BaseRenderer):
    """Simple DRF renderer allowing `?format=csv` content negotiation for CSV exports."""
    media_type = "text/csv"
    format = "csv"
    charset = "utf-8"

    def render(self, data: Any, accepted_media_type: str = None, renderer_context: Any = None) -> bytes:
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
        return str(data).encode("utf-8")


from apps.data_engine.application.dto import (
    ImportRequest,
    ValidationRequest,
)
from apps.data_engine.application.facade import MacApplicationFacade
from .permissions import IsTenantAuthorized
from .serializers import (
    ErrorExportRequestSerializer,
    EventListResponseSerializer,
    ImportResponseSerializer,
    ImportStartSerializer,
    PreviewRequestSerializer,
    PreviewResponseSerializer,
    ProgressResponseSerializer,
    SessionResponseSerializer,
    ValidationRequestSerializer,
    ValidationResponseSerializer,
)


class ImportSessionViewSet(viewsets.ViewSet):
    """ViewSet managing lifecycle, monitoring, and controls of MAC import sessions."""
    permission_classes = [permissions.IsAuthenticated, IsTenantAuthorized]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.facade = MacApplicationFacade()

    def create(self, request: Request) -> Response:
        """Start a new import workflow session.

        POST /api/data-engine/sessions/
        """
        serializer = ImportStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_id = data.get("user_id")
        if not user_id and request.user and request.user.is_authenticated:
            user_id = getattr(request.user, "username", None) or str(getattr(request.user, "id", ""))
        user_id = user_id or "system_operator"

        req_dto = ImportRequest(
            tenant_id=data["tenant_id"],
            user_id=user_id,
            source=data["source"],
            pipeline_config=data.get("pipeline_config", {}),
            run_id=data.get("run_id"),
            is_dry_run=data.get("is_dry_run", False),
        )

        res_dto = self.facade.start_import(req_dto)
        out_serializer = ImportResponseSerializer({
            "session_id": res_dto.session_id,
            "run_id": res_dto.run_id,
            "state": res_dto.state,
            "total_records": res_dto.total_records,
            "processed_records": res_dto.processed_records,
            "errors": res_dto.errors,
            "is_success": res_dto.is_success,
        })
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request: Request, pk: str = None) -> Response:
        """Retrieve state and phase summary report for a session.

        GET /api/data-engine/sessions/{pk}/
        """
        res_dto = self.facade.get_session(pk)
        out_serializer = SessionResponseSerializer({
            "session_id": res_dto.session_id,
            "tenant_id": res_dto.tenant_id,
            "user_id": res_dto.user_id,
            "state": res_dto.state,
            "phases": res_dto.phases,
        })
        return Response(out_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def resume(self, request: Request, pk: str = None) -> Response:
        """Resume a paused or interrupted import session.

        POST /api/data-engine/sessions/{pk}/resume/
        """
        res_dto = self.facade.resume(pk)
        out_serializer = ImportResponseSerializer({
            "session_id": res_dto.session_id,
            "run_id": res_dto.run_id,
            "state": res_dto.state,
            "total_records": res_dto.total_records,
            "processed_records": res_dto.processed_records,
            "errors": res_dto.errors,
            "is_success": res_dto.is_success,
        })
        return Response(out_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request: Request, pk: str = None) -> Response:
        """Abort/Cancel an active import session.

        POST /api/data-engine/sessions/{pk}/cancel/
        """
        res_dto = self.facade.cancel(pk)
        out_serializer = ImportResponseSerializer({
            "session_id": res_dto.session_id,
            "run_id": res_dto.run_id,
            "state": res_dto.state,
            "total_records": res_dto.total_records,
            "processed_records": res_dto.processed_records,
            "errors": res_dto.errors,
            "is_success": res_dto.is_success,
        })
        return Response(out_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def progress(self, request: Request, pk: str = None) -> Response:
        """Retrieve real-time progress metrics snapshot for a session.

        GET /api/data-engine/sessions/{pk}/progress/
        """
        res_dto = self.facade.get_progress(pk)
        out_serializer = ProgressResponseSerializer({
            "session_id": res_dto.session_id,
            "run_id": res_dto.run_id,
            "state": res_dto.state,
            "current_phase": res_dto.current_phase,
            "percentage": res_dto.percentage,
            "processed": res_dto.processed,
            "total": res_dto.total,
            "accepted": res_dto.accepted,
            "rejected": res_dto.rejected,
            "elapsed_ms": res_dto.elapsed_ms,
            "eta_seconds": res_dto.eta_seconds,
            "throughput": res_dto.throughput,
        })
        return Response(out_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def events(self, request: Request, pk: str = None) -> Response:
        """Retrieve buffered event envelopes for a session (replay capability).

        GET /api/data-engine/sessions/{pk}/events/?since_sequence=0
        """
        try:
            since_seq = int(request.query_params.get("since_sequence", 0))
        except (ValueError, TypeError):
            since_seq = 0

        res_dto = self.facade.get_events(pk, since_sequence=since_seq)
        out_serializer = EventListResponseSerializer({
            "session_id": res_dto.session_id,
            "events": res_dto.events,
        })
        return Response(out_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="errors/export", renderer_classes=[renderers.JSONRenderer, CSVRenderer])
    def export_errors(self, request: Request, pk: str = None) -> HttpResponse:
        """Export session errors as CSV or JSON payload.

        GET /api/data-engine/sessions/{pk}/errors/export/?format=csv|json
        """
        serializer = ErrorExportRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        fmt = serializer.validated_data["format"]

        res_dto = self.facade.export_errors(pk, format_type=fmt)

        if fmt == "json":
            response = HttpResponse(res_dto.data, content_type="application/json")
            response["Content-Disposition"] = f'attachment; filename="errors_{pk}.json"'
        else:
            response = HttpResponse(res_dto.data, content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="errors_{pk}.csv"'
        return response


class ValidationAPIView(APIView):
    """API endpoint for pre-import data and schema rule validation."""
    permission_classes = [permissions.IsAuthenticated, IsTenantAuthorized]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.facade = MacApplicationFacade()

    def post(self, request: Request) -> Response:
        """Execute validation rules without running full import.

        POST /api/data-engine/validate/
        """
        serializer = ValidationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        req_dto = ValidationRequest(
            tenant_id=data["tenant_id"],
            source=data["source"],
            rules=data.get("rules", []),
        )
        res_dto = self.facade.validate(req_dto)
        out_serializer = ValidationResponseSerializer({
            "is_valid": res_dto.is_valid,
            "total_checked": res_dto.total_checked,
            "violations": res_dto.violations,
        })
        return Response(out_serializer.data, status=status.HTTP_200_OK)


class PreviewAPIView(APIView):
    """API endpoint for inspecting and sampling rows from data sources."""
    permission_classes = [permissions.IsAuthenticated, IsTenantAuthorized]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.facade = MacApplicationFacade()

    def post(self, request: Request) -> Response:
        """Inspect headers and sample rows up to `limit`.

        POST /api/data-engine/preview/
        """
        serializer = PreviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        res_dto = self.facade.preview(source=data["source"], limit=data["limit"])
        out_serializer = PreviewResponseSerializer({
            "headers": res_dto.headers,
            "sample_rows": res_dto.sample_rows,
            "total_preview_records": res_dto.total_preview_records,
        })
        return Response(out_serializer.data, status=status.HTTP_200_OK)
