# apps/data_engine/quality/base.py
"""Abstract base interfaces for the Data Quality Rules Engine."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from apps.data_engine.quality.models import QualityViolation, QualityReport


class BaseQualityRule(ABC):
    """Abstract interface representing a data quality validation rule."""

    @property
    @abstractmethod
    def code(self) -> str:
        """Return the unique code identifier of this rule (e.g. 'REQUIRED_FIELD')."""
        pass

    @property
    @abstractmethod
    def field(self) -> Optional[str]:
        """Return the field name targeted by this rule, if applicable."""
        pass

    @property
    @abstractmethod
    def severity(self) -> str:
        """Return severity level: INFO, WARNING, ERROR, or CRITICAL."""
        pass

    @abstractmethod
    def validate(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[QualityViolation]:
        """Validate a single record and return a list of QualityViolation occurrences."""
        pass


class BaseQualityEngine(ABC):
    """Abstract interface for the central evaluation engine."""

    @abstractmethod
    def execute(
        self,
        records: List[Dict[str, Any]],
        session_id: str,
        template_code: str,
        rules: Optional[List[BaseQualityRule]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> QualityReport:
        """Evaluate a set of records against rules and return a comprehensive QualityReport."""
        pass


class BaseQualityScorer(ABC):
    """Abstract interface for calculating quantitative data quality metrics."""

    @abstractmethod
    def calculate_record_score(self, violations: List[QualityViolation]) -> float:
        """Calculate score (0-100) for a single record based on violations."""
        pass

    @abstractmethod
    def calculate_aggregate_score(self, record_scores: List[float]) -> float:
        """Calculate overall aggregated quality score (0-100) across all records."""
        pass


class BaseQualityReporter(ABC):
    """Abstract interface for exporting quality engine execution reports."""

    @abstractmethod
    def generate(self, report: QualityReport) -> str:
        """Serialize a QualityReport into a targeted string format (JSON, CSV, summary text, etc.)."""
        pass
