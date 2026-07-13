# apps/data_engine/quality/__init__.py
"""Enterprise Data Quality Rules Engine & Governance subsystem."""

from .base import BaseQualityRule, BaseQualityEngine, BaseQualityScorer, BaseQualityReporter
from .contracts import QualityEvaluator
from .models import QualityViolation, QualityRuleResult, QualityStatistics, QualityScore, QualityReport
from .exceptions import QualityException, RuleException, ScoringException, ReportingException
from .registry import QualityRuleRegistry
from .scorer import QualityScorer
from .reporters import JsonQualityReporter, CsvQualityReporter, SummaryQualityReporter
from .engine import QualityEngine, QualityRuleTransformationAdapter, QualityWorkflowComponent
from .rules import (
    RequiredRule,
    RegexRule,
    RangeRule,
    EnumRule,
    UniqueRule,
    LengthRule,
    EmailRule,
    DateRule,
    NumericRule,
    ReferenceRule,
    CompositeRule,
    ConditionalRule,
)

__all__ = [
    "BaseQualityRule",
    "BaseQualityEngine",
    "BaseQualityScorer",
    "BaseQualityReporter",
    "QualityEvaluator",
    "QualityViolation",
    "QualityRuleResult",
    "QualityStatistics",
    "QualityScore",
    "QualityReport",
    "QualityException",
    "RuleException",
    "ScoringException",
    "ReportingException",
    "QualityRuleRegistry",
    "QualityScorer",
    "JsonQualityReporter",
    "CsvQualityReporter",
    "SummaryQualityReporter",
    "QualityEngine",
    "QualityRuleTransformationAdapter",
    "QualityWorkflowComponent",
    "RequiredRule",
    "RegexRule",
    "RangeRule",
    "EnumRule",
    "UniqueRule",
    "LengthRule",
    "EmailRule",
    "DateRule",
    "NumericRule",
    "ReferenceRule",
    "CompositeRule",
    "ConditionalRule",
]
