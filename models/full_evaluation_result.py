"""Full evaluation result aggregating all agent outputs."""

from datetime import datetime
from dataclasses import dataclass, field
from .startup_profile import StartupProfile
from .analysis_results import (
    TechnologyAnalysisResult,
    MarketabilityAnalysisResult,
    ImpactAnalysisResult,
    DataMoatAnalysisResult,
)
from .competitor_result import CompetitorAnalysisResult
from .decision_result import InvestmentDecision


@dataclass
class FullEvaluationResult:
    """Complete evaluation report for a startup."""

    startup: StartupProfile
    technology_analysis: TechnologyAnalysisResult
    marketability_analysis: MarketabilityAnalysisResult
    impact_analysis: ImpactAnalysisResult
    data_moat_analysis: DataMoatAnalysisResult
    competitor_analysis: CompetitorAnalysisResult
    investment_decision: InvestmentDecision
    report_content: str = ""
    evaluation_timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "startup": {
                "name": self.startup.name,
                "founded_year": self.startup.founded_year,
                "stage": self.startup.stage,
            },
            "technology": {
                "novelty_score": self.technology_analysis.novelty_score,
                "defensibility_score": self.technology_analysis.defensibility_score,
            },
            "marketability": {
                "market_growth_potential": self.marketability_analysis.market_growth_potential,
                "commercial_feasibility_score": self.marketability_analysis.commercial_feasibility_score,
            },
            "impact": {
                "environmental_impact": self.impact_analysis.environmental_impact,
                "agricultural_impact": self.impact_analysis.agricultural_impact,
            },
            "data_moat": {
                "moat_strength_score": self.data_moat_analysis.moat_strength_score,
            },
            "competitor": {
                "competitive_advantage_score": self.competitor_analysis.competitive_advantage_score,
            },
            "decision": {
                "recommendation": self.investment_decision.recommendation.value,
                "confidence_score": self.investment_decision.confidence_score,
                "overall_assessment_score": self.investment_decision.overall_assessment_score,
            },
            "timestamp": self.evaluation_timestamp.isoformat(),
        }
