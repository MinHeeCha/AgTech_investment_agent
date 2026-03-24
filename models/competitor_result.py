"""Competitor analysis result data model."""

from dataclasses import dataclass, field
from .evidence_item import EvidenceItem


@dataclass
class CompetitorAnalysisResult:
    """Result from Competitor Comparison Agent."""

    comparable_competitors: list[str] = field(default_factory=list)
    comparable_competitor_scores: dict[str, float] = field(default_factory=dict)
    technology_differentiation: str = ""
    technology_differentiation_score: float = 0.0  # 0.0 to 1.0
    market_position_analysis: str = ""
    relative_barriers_to_entry: float = 0.0  # 0.0 to 1.0
    relative_strengths: list[str] = field(default_factory=list)
    relative_weaknesses: list[str] = field(default_factory=list)
    competitive_advantage_score: float = 0.0  # 0.0 to 1.0
    evidence: list[EvidenceItem] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    summary: str = ""
