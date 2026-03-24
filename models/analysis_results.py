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
    """Result from Impact Evaluation Agent.

    E. 임팩트 & 지속가능성 (총 15점)
      sdg2_score         : SDG 2 기여도   — 0 / 3 / 6
      carbon_water_score : 탄소·물 감축   — 0 / 2 / 5
      esg_score          : ESG 투자자 어필 — 0 / 2 / 4

    agricultural_impact  = sdg2_score / 6          (0.0–1.0, step3 투자 결정 기준)
    environmental_impact = carbon_water_score / 5  (0.0–1.0)
    """

    # Rubric scores (E항목)
    sdg2_score: int = 0            # 0 / 3 / 6
    carbon_water_score: int = 0    # 0 / 2 / 5
    esg_score: int = 0             # 0 / 2 / 4
    total_impact_score: int = 0    # 0–15

    # Score rationale
    sdg2_reason: str = ""
    carbon_water_reason: str = ""
    esg_reason: str = ""

    # Derived floats (used by downstream agents)
    environmental_impact: float = 0.0  # carbon_water_score / 5
    agricultural_impact: float = 0.0   # sdg2_score / 6

    # Detailed claims
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

    moat_type: str = "data"                  # "data" | "ip"
    dataset_size_level: str = "small"        # "large" | "medium" | "small"
    dataset_size_description: str = ""
    contract_level: str = "none"             # "exclusive" | "non_exclusive" | "none"
    contract_description: str = ""
    network_effect_level: str = "none"       # "auto" | "manual" | "none"
    network_effect_description: str = ""
    dataset_size_score: int = 0              # /8
    exclusive_contract_score: int = 0        # /7
    network_effect_score: int = 0            # /5
    total_score: int = 0                     # /20

    # IP 해자 전환 시 사용하는 필드들
    ip_moat_note: str = ""
    patent_count: str = "미확인"
    field_trial_description: str = ""
    big_corp_partnership: str = ""
