# apps/data_engine/api/serializers.py
"""DRF Serializers for the Motor de Análisis y Carga (MAC) API Gateway.

Validates incoming REST request payloads (`ImportRequest`, `ValidationRequest`, etc.)
and formats outgoing DTO representations into clean, API-friendly JSON structures.
"""

from typing import Any, Dict, List
from rest_framework import serializers


# ==============================================================================
# Input Request Serializers
# ==============================================================================

class ImportStartSerializer(serializers.Serializer):
    """Validates payload for starting a new import workflow session."""
    tenant_id = serializers.CharField(required=True, max_length=100)
    user_id = serializers.CharField(required=False, allow_blank=True, max_length=100)
    source = serializers.JSONField(required=True, help_text="Data source: file path string, list of dicts, or dictionary.")
    pipeline_config = serializers.DictField(required=False, default=dict)
    run_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=100)
    is_dry_run = serializers.BooleanField(required=False, default=False)


class ValidationRequestSerializer(serializers.Serializer):
    """Validates payload for executing pre-import validation rules."""
    tenant_id = serializers.CharField(required=True, max_length=100)
    source = serializers.JSONField(required=True)
    rules = serializers.ListField(
        child=serializers.CharField(max_length=150),
        required=False,
        default=list,
    )


class PreviewRequestSerializer(serializers.Serializer):
    """Validates payload for previewing sample rows from a data source."""
    source = serializers.JSONField(required=True)
    limit = serializers.IntegerField(required=False, default=10, min_value=1, max_value=1000)


class ErrorExportRequestSerializer(serializers.Serializer):
    """Validates query parameters for exporting session errors."""
    format = serializers.ChoiceField(choices=["csv", "json"], required=False, default="csv")


# ==============================================================================
# Output Response Serializers
# ==============================================================================

class ImportResponseSerializer(serializers.Serializer):
    """Formats `ImportResponse` DTO to JSON."""
    session_id = serializers.CharField()
    run_id = serializers.CharField()
    state = serializers.CharField()
    total_records = serializers.IntegerField()
    processed_records = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField())
    is_success = serializers.BooleanField()


class ValidationViolationSerializer(serializers.Serializer):
    rule = serializers.CharField()
    error = serializers.CharField()


class ValidationResponseSerializer(serializers.Serializer):
    """Formats `ValidationResponse` DTO to JSON."""
    is_valid = serializers.BooleanField()
    total_checked = serializers.IntegerField()
    violations = serializers.ListField(child=serializers.DictField())


class PreviewResponseSerializer(serializers.Serializer):
    """Formats `PreviewResponse` DTO to JSON."""
    headers = serializers.ListField(child=serializers.CharField())
    sample_rows = serializers.ListField(child=serializers.DictField())
    total_preview_records = serializers.IntegerField()


class ProgressResponseSerializer(serializers.Serializer):
    """Formats `ProgressResponse` DTO to JSON."""
    session_id = serializers.CharField()
    run_id = serializers.CharField()
    state = serializers.CharField()
    current_phase = serializers.CharField()
    percentage = serializers.FloatField()
    processed = serializers.IntegerField()
    total = serializers.IntegerField()
    accepted = serializers.IntegerField()
    rejected = serializers.IntegerField()
    elapsed_ms = serializers.FloatField()
    eta_seconds = serializers.FloatField()
    throughput = serializers.FloatField()


class PhaseSummarySerializer(serializers.Serializer):
    phase_name = serializers.CharField()
    success = serializers.BooleanField()
    input_records = serializers.IntegerField()
    output_records = serializers.IntegerField()
    duration_ms = serializers.FloatField()
    errors = serializers.ListField(child=serializers.CharField())


class SessionResponseSerializer(serializers.Serializer):
    """Formats `SessionResponse` DTO to JSON."""
    session_id = serializers.CharField()
    tenant_id = serializers.CharField()
    user_id = serializers.CharField()
    state = serializers.CharField()
    phases = serializers.ListField(child=serializers.DictField())


class EventListResponseSerializer(serializers.Serializer):
    """Formats `EventListResponse` DTO to JSON."""
    session_id = serializers.CharField()
    events = serializers.ListField(child=serializers.DictField())
