# apps/data_engine/events/__init__.py
"""Real-Time Event Bus & Notification Framework for MAC.

Provides a unified, transport-agnostic event distribution channel across
the entire MAC pipeline.  Supports category-based filtering, per-session
replay buffering, and extensible subscriber implementations for WebSocket,
SSE, Redis Pub/Sub, or any future transport.  Strictly decoupled from
Django ORM (Zero-ORM policy).
"""

from .base import BaseEventDispatcher, BaseEventSubscriber
from .models import EventCategory, EventEnvelope

__all__ = [
    "BaseEventDispatcher",
    "BaseEventSubscriber",
    "EventCategory",
    "EventEnvelope",
]
