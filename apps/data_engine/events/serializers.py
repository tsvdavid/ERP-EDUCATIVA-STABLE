# apps/data_engine/events/serializers.py
"""Serialization utilities for the MAC Event Bus.

Provides JSON round-trip serialization for ``EventEnvelope`` instances and
conversion helpers to bridge ``ProgressEvent`` objects from TAREA 20 into
the universal ``EventEnvelope`` format.
"""

import json
from typing import Any, Dict

from apps.data_engine.progress.models import ProgressEvent

from .models import EventCategory, EventEnvelope


class EventSerializer:
    """Stateless serializer for ``EventEnvelope`` instances."""

    @staticmethod
    def envelope_to_json(envelope: EventEnvelope) -> str:
        """Serialize an ``EventEnvelope`` to a JSON string."""
        return json.dumps(envelope.to_dict(), ensure_ascii=False, default=str)

    @staticmethod
    def envelope_from_dict(data: Dict[str, Any]) -> EventEnvelope:
        """Reconstruct an ``EventEnvelope`` from a dictionary (e.g. parsed JSON)."""
        return EventEnvelope(
            envelope_id=data["envelope_id"],
            category=EventCategory(data["category"]),
            event_type=data["event_type"],
            session_id=data["session_id"],
            timestamp=data["timestamp"],
            payload=dict(data.get("payload", {})),
            source=data["source"],
            sequence_number=int(data["sequence_number"]),
            tenant_id=data.get("tenant_id"),
            institution_id=data.get("institution_id"),
            metadata=dict(data.get("metadata", {})),
        )

    @staticmethod
    def progress_event_to_envelope(
        event: ProgressEvent,
        sequence_number: int = 0,
    ) -> EventEnvelope:
        """Convert a ``ProgressEvent`` (TAREA 20) into an ``EventEnvelope``."""
        return EventEnvelope.create(
            category=EventCategory.PROGRESS,
            event_type=event.event_type.value,
            session_id=event.session_id,
            payload=event.to_dict(),
            source="progress",
            sequence_number=sequence_number,
            metadata=dict(event.metadata) if event.metadata else {},
        )
