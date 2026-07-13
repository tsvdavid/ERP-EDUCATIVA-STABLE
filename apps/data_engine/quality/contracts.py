# apps/data_engine/quality/contracts.py
"""Public contracts, protocol classes and typings for the Quality Engine."""

from typing import Any, Dict, List, Protocol, runtime_checkable
from apps.data_engine.quality.models import QualityViolation


@runtime_checkable
class QualityEvaluator(Protocol):
    """Protocol defining runtime evaluation of record structures."""

    def evaluate_record(self, record: Dict[str, Any]) -> List[QualityViolation]:
        """Perform evaluation checks on a record dictionary."""
        ...
