"""Analysis result data models."""

from typing import Optional
from dataclasses import dataclass, field
from .evidence_item import EvidenceItem


@dataclass
class TechnologyAnalysisResult:
    """Result from Technology Summary Agent."""

    core_technology: str
    novelty_score: float  # 0.0 to 1.0
    defensibility_score: float  # 0.0 to 1.0
    patents: list[str] = field(default_factory=list)
    research_papers: list[str] = field(default_factory=list)
    technical_keywords: list[str] = field(default_factory=list)
    evidence: list[EvidenceItem] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class MarketabilityAnalysisResult:
    """Result from Marketability Evaluation Agent."""

    target_market_size: Optional[str] = None
    market_growth_potential: float = 0.0  # 0.0 to 1.0
    customer_pain_points: list[str] = field(default_factory=list)
    business_model: Optional[str] = None
    adoption_barriers: list[str] = field(default_factory=list)
    commercial_feasibility_score: float = 0.0  # 0.0 to 1.0
    evidence: list[EvidenceItem] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class ImpactAnalysisResult:
    """Result from Impact Evaluation Agent."""

    environmental_impact: float = 0.0  # 0.0 to 1.0
    agricultural_impact: float = 0.0  # 0.0 to 1.0
    sustainability_focus: list[str] = field(default_factory=list)
    efficiency_improvements: list[str] = field(default_factory=list)
    yield_improvement_claimed: Optional[str] = None
    carbon_reduction_claimed: Optional[str] = None
    water_saving_claimed: Optional[str] = None
    evidence: list[EvidenceItem] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class DataMoatAnalysisResult:
    """Result from Data Moat Analysis Agent."""

    has_proprietary_datasets: bool = False
    dataset_defensibility_score: float = 0.0  # 0.0 to 1.0
    data_flywheel_potential: float = 0.0  # 0.0 to 1.0
    sensing_pipeline_uniqueness: str = ""
    data_assets_description: str = ""
    moat_strength_score: float = 0.0  # 0.0 to 1.0
    evidence: list[EvidenceItem] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    summary: str = ""
