# apps/data_engine/quality/scorer.py
"""Concrete scorer implementing standard severity-based quality points deduction."""

from typing import List
from apps.data_engine.quality.base import BaseQualityScorer
from apps.data_engine.quality.models import QualityScore, QualityViolation


class QualityScorer(BaseQualityScorer):
    """Calculates record and aggregate quality scores on a scale of 0-100."""

    def calculate_record_score(self, violations: List[QualityViolation]) -> float:
        """Subtract points for each violation based on severity. Caps score [0, 100]."""
        score = 100.0
        for v in violations:
            sev = v.severity.upper()
            if sev == "INFO":
                score -= 1.0
            elif sev == "WARNING":
                score -= 10.0
            elif sev == "ERROR":
                score -= 30.0
            elif sev == "CRITICAL":
                score -= 100.0
        return max(0.0, min(100.0, score))

    def calculate_aggregate_score(self, record_scores: List[float]) -> float:
        """Calculate arithmetic mean of all individual record scores. Defaults to 100.0."""
        if not record_scores:
            return 100.0
        return sum(record_scores) / len(record_scores)

    def determine_rating(self, score: float) -> str:
        """Determine qualitative rating for a numerical score."""
        if score >= 90.0:
            return "EXCELLENT"
        elif score >= 70.0:
            return "GOOD"
        elif score >= 50.0:
            return "FAIR"
        else:
            return "POOR"

    def score_run(self, violations_by_record: dict, total_records: int) -> QualityScore:
        """Calculate overall QualityScore DTO."""
        record_scores: List[float] = []
        for i in range(total_records):
            violations = violations_by_record.get(i, [])
            record_scores.append(self.calculate_record_score(violations))
        
        agg_score = self.calculate_aggregate_score(record_scores)
        rating = self.determine_rating(agg_score)
        return QualityScore(score=agg_score, rating=rating)
