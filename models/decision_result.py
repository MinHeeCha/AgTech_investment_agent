"""Investment decision result data model."""

from enum import Enum
from dataclasses import dataclass, field
from .evidence_item import EvidenceItem


class InvestmentRecommendation(str, Enum):
    """Investment recommendation options."""

    INVEST = "invest"
    HOLD_FOR_REVIEW = "hold_for_review"
    PASS = "pass"


@dataclass
class InvestmentDecision:
    """Result from Investment Decision Agent."""

    recommendation: InvestmentRecommendation
    confidence_score: float  # 0.0 to 1.0
    overall_assessment_score: float  # 0.0 to 1.0
    key_strengths: list[str] = field(default_factory=list)
    key_risks: list[str] = field(default_factory=list)
    missing_critical_information: list[str] = field(default_factory=list)
    rationale: str = ""
    evidence: list[EvidenceItem] = field(default_factory=list)
    evidence_gaps: list[str] = field(default_factory=list)
    evaluated_top_companies: list[str] = field(default_factory=list)
    qualified_companies: list[str] = field(default_factory=list)
    company_scorecard: dict[str, float] = field(default_factory=dict)
