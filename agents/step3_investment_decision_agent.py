"""Investment Decision Agent - Makes investment recommendations."""

from typing import Optional
from models import (
    InvestmentDecision, InvestmentRecommendation, EvidenceItem, StartupProfile,
    TechnologyAnalysisResult, MarketabilityAnalysisResult, ImpactAnalysisResult,
    DataMoatAnalysisResult, CompetitorAnalysisResult
)
from evaluation import EvaluationCriteria, ScoringRules, InvestmentThresholds
from .base_agent import BaseAgent


class InvestmentDecisionAgent(BaseAgent):
    """Agent responsible for making investment recommendations."""

    MIN_QUALIFIED_SCORE = 0.60
    STRONG_QUALIFIED_SCORE = 0.75

    def __init__(self):
        super().__init__(
            name="InvestmentDecisionAgent",
            description="Integrates all analysis and produces investment decision",
        )

    @classmethod
    def _evaluate_top_companies(
        cls,
        competitor_analysis: CompetitorAnalysisResult
    ) -> tuple[list[str], list[str], dict[str, float]]:
        """
        Evaluate top-3 companies against step3 score criteria.

        Criteria:
        - qualified: total_score >= 0.60
        - strong qualified: total_score >= 0.75
        """
        top_companies = competitor_analysis.comparable_competitors[:3]
        top_scores = competitor_analysis.comparable_competitor_scores or {}

        scorecard = {
            company_name: float(top_scores.get(company_name, 0.0))
            for company_name in top_companies
        }
        qualified_companies = [
            company_name
            for company_name, score in scorecard.items()
            if score >= cls.MIN_QUALIFIED_SCORE
        ]
        strong_qualified_companies = [
            company_name
            for company_name, score in scorecard.items()
            if score >= cls.STRONG_QUALIFIED_SCORE
        ]
        return qualified_companies, strong_qualified_companies, scorecard

    def execute(self,
               startup: StartupProfile,
               tech_analysis: TechnologyAnalysisResult,
               market_analysis: MarketabilityAnalysisResult,
               impact_analysis: ImpactAnalysisResult,
               data_moat_analysis: DataMoatAnalysisResult,
               competitor_analysis: CompetitorAnalysisResult) -> InvestmentDecision:
        """
        Produce investment decision.

        Args:
            startup: Startup profile
            tech_analysis: Technology analysis results
            market_analysis: Market analysis results
            impact_analysis: Impact analysis results
            data_moat_analysis: Data moat analysis results
            competitor_analysis: Competitor analysis results

        Returns:
            InvestmentDecision
        """
        self.start_execution()

        try:
            self.log_info(f"Making investment decision for {startup.name}")

            # Aggregate scores from all analyses
            category_scores = {
                "technology": (tech_analysis.novelty_score + tech_analysis.defensibility_score) / 2,
                "market": market_analysis.commercial_feasibility_score,
                "impact": impact_analysis.environmental_impact,
                "data_moat": data_moat_analysis.moat_strength_score,
                "competitive": competitor_analysis.competitive_advantage_score,
            }

            # Calculate overall assessment score
            overall_score = ScoringRules.aggregate_scores(
                category_scores,
                EvaluationCriteria.OVERALL_WEIGHTS
            )

            # Calculate confidence based on evidence quantity and consistency
            evidence_count = (len(tech_analysis.evidence) + len(market_analysis.evidence) +
                            len(impact_analysis.evidence) + len(data_moat_analysis.evidence) +
                            len(competitor_analysis.evidence))
            confidence = min(0.95, 0.4 + (evidence_count * 0.05))

            # Count critical information gaps
            critical_gaps = (len(tech_analysis.missing_information) +
                           len(market_analysis.missing_information) +
                           len(impact_analysis.missing_information))

            # Get recommendation
            recommendation_str = InvestmentThresholds.get_recommendation(
                overall_score, confidence, critical_gaps
            )
            recommendation = InvestmentRecommendation(recommendation_str)

            # Evaluate the top-3 companies returned by step2.
            qualified_companies, strong_qualified_companies, scorecard = self._evaluate_top_companies(
                competitor_analysis
            )
            startup_qualified = startup.name in qualified_companies

            # Identify key strengths
            strengths = []
            if tech_analysis.novelty_score > 0.65:
                strengths.append(f"Strong technology novelty ({tech_analysis.novelty_score:.2f})")
            if market_analysis.market_growth_potential > 0.70:
                strengths.append(f"Large market opportunity (Growth: {market_analysis.market_growth_potential:.2f})")
            if impact_analysis.agricultural_impact > 0.70:
                strengths.append("Significant agricultural impact")
            if data_moat_analysis.moat_strength_score > 0.60:
                strengths.append("Defendable competitive position")
            if startup_qualified:
                strengths.append(
                    f"Passed step3 qualification threshold ({self.MIN_QUALIFIED_SCORE:.2f}) "
                    f"within top-3 companies"
                )
            if startup.name in strong_qualified_companies:
                strengths.append(
                    f"Strongly qualified in top-3 cohort ({self.STRONG_QUALIFIED_SCORE:.2f}+)"
                )

            # Identify key risks
            risks = []
            if tech_analysis.novelty_score < 0.50:
                risks.append("Limited technical differentiation")
            if market_analysis.commercial_feasibility_score < 0.50:
                risks.append("Commercialization challenges")
            if critical_gaps > 2:
                risks.append(f"Multiple critical information gaps ({critical_gaps})")
            if competitor_analysis.competitive_advantage_score < 0.50:
                risks.append("Weak competitive positioning")
            if not startup_qualified:
                risks.append(
                    f"Did not meet step3 qualification threshold ({self.MIN_QUALIFIED_SCORE:.2f}) "
                    "within top-3 companies"
                )

            # Collect all evidence
            all_evidence = (tech_analysis.evidence + market_analysis.evidence +
                         impact_analysis.evidence + data_moat_analysis.evidence +
                         competitor_analysis.evidence)

            # Create decision
            decision = InvestmentDecision(
                recommendation=recommendation,
                confidence_score=confidence,
                overall_assessment_score=overall_score,
                key_strengths=strengths,
                key_risks=risks,
                missing_critical_information=[
                    f"Technology: {tech_analysis.missing_information}",
                    f"Market: {market_analysis.missing_information}",
                    f"Impact: {impact_analysis.missing_information}",
                ],
                evidence=all_evidence[:10],  # Top 10 evidence items
                evidence_gaps=[
                    item for item in
                    tech_analysis.missing_information + market_analysis.missing_information +
                    impact_analysis.missing_information + data_moat_analysis.missing_information
                ],
                evaluated_top_companies=competitor_analysis.comparable_competitors[:3],
                qualified_companies=qualified_companies,
                company_scorecard=scorecard,
            )

            # Build rationale
            decision.rationale = f"Decision: {recommendation_str.upper()}. " \
                               f"Overall Score: {overall_score:.2f}. " \
                               f"Confidence: {confidence:.2f}. " \
                               f"Qualified companies (>= {self.MIN_QUALIFIED_SCORE:.2f}): " \
                               f"{', '.join(qualified_companies) if qualified_companies else 'None'}. " \
                               f"Key strengths: {', '.join(strengths[:2])}. " \
                               f"Key risks: {', '.join(risks[:2])}"

            self.log_info(f"Investment decision complete: {recommendation_str}")
            self.log_info(f"Overall Assessment Score: {overall_score:.2f}")
            self.log_info(f"Confidence: {confidence:.2f}")

            return decision

        finally:
            self.end_execution()
