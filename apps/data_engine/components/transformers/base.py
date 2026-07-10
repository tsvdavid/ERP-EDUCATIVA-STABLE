# apps/data_engine/components/transformers/base.py
"""Base class for MAC transformers.

Transformers are a specialised type of ``BaseComponent`` that focus on
normalising or enriching the ``payload`` within a ``MacContext``.
"""

from apps.data_engine.components.base import BaseComponent

class BaseTransformer(BaseComponent):
    """Abstract base for all transformer components.

    No additional abstract methods are required – ``execute`` is already
    defined abstract in ``BaseComponent``. Sub‑classes should be stateless.
    """
    pass
