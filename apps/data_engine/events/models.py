# apps/data_engine/events/models.py
"""Domain models for the Real-Time Event Bus & Notification Framework.

Provides the universal event container (`EventEnvelope`) and event taxonomy
(`EventCategory`) for distributing all MAC events through a single, unified
channel.  Strictly decoupled from Django ORM (Zero-ORM policy).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class EventCategory(str, Enum):
    """Unified taxonomy of MAC event categories.

    Allows subscribers to filter by broad category while the ``event_type``
    string provides granular specificity within each category.
    """

    PROGRESS = "PROGRESS"
    SESSION = "SESSION"
    EXECUTION = "EXECUTION"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class EventEnvelope:
    """Immutable universal container for any event emitted by the MAC pipeline.

    Designed to be serialized and transmitted over any transport protocol
    (REST, WebSocket, SSE, Redis Pub/Sub, Kafka, etc.) without coupling
    the MAC core to any specific implementation.

    Attributes
    ----------
    envelope_id : str
        Unique UUID identifying this specific event envelope instance.
    category : EventCategory
        Broad taxonomic category (PROGRESS, SESSION, EXECUTION, SYSTEM).
    event_type : str
        Granular type identifier (e.g. ``"PHASE_PROGRESS"``, ``"SESSION_START"``).
    session_id : str
        Identifier of the import session that originated this event.
    timestamp : str
        ISO-8601 UTC timestamp when the envelope was created.
    payload : Dict[str, Any]
        JSON-serializable event data (snapshot, metadata, error details, etc.).
    source : str
        Originating module within the MAC pipeline (``"progress"``, ``"session"``,
        ``"execution"``, ``"system"``).
    sequence_number : int
        Monotonically increasing per-session sequence number.  Enables ordered
        replay and gap detection by consumers that reconnect.
    metadata : Dict[str, Any]
        Optional auxiliary data (routing hints, tenant context, etc.).
    """

    envelope_id: str
    category: EventCategory
    event_type: str
    session_id: str
    timestamp: str
    payload: Dict[str, Any]
    source: str
    sequence_number: int
    tenant_id: Optional[str] = None
    institution_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        category: EventCategory,
        event_type: str,
        session_id: str,
        payload: Dict[str, Any],
        source: str,
        sequence_number: int = 0,
        tenant_id: Optional[str] = None,
        institution_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "EventEnvelope":
        """Factory helper to create a new ``EventEnvelope`` with auto-generated ID and timestamp."""
        return cls(
            envelope_id=str(uuid.uuid4()),
            category=category,
            event_type=event_type,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=dict(payload),
            source=source,
            sequence_number=sequence_number,
            tenant_id=tenant_id,
            institution_id=institution_id,
            metadata=dict(metadata) if metadata else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the envelope to a clean JSON-serializable dictionary."""
        result: Dict[str, Any] = {
            "envelope_id": self.envelope_id,
            "category": self.category.value,
            "event_type": self.event_type,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "payload": dict(self.payload),
            "source": self.source,
            "sequence_number": self.sequence_number,
            "metadata": dict(self.metadata),
        }
        if self.tenant_id is not None:
            result["tenant_id"] = self.tenant_id
        if self.institution_id is not None:
            result["institution_id"] = self.institution_id
        return result
