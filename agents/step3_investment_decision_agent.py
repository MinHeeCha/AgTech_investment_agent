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
                "market": market_analysis.commercial_feasibility_score / 25.0,
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
                strengths.append(f"기술 혁신성 우수 (참신성 {tech_analysis.novelty_score:.0%})")
            if market_analysis.market_growth_potential > 7.7:
                strengths.append(f"대규모 성장 시장 (성장 잠재력 {market_analysis.market_growth_potential / 11.0:.0%})")
            if impact_analysis.agricultural_impact > 0.70:
                strengths.append("농업 생산성 및 식량 안보에 대한 실질적 기여")
            if data_moat_analysis.moat_strength_score > 0.60:
                strengths.append(f"방어 가능한 경쟁 위치 (해자 점수 {data_moat_analysis.moat_strength_score:.0%})")
            if startup_qualified:
                strengths.append("상위 3개 기업 선정 — 투자 적격 기준 통과")
            if startup.name in strong_qualified_companies:
                strengths.append("상위 3개 기업 중 강력 투자 적격 (75%+ 점수)")

            # Identify key risks
            risks = []
            if tech_analysis.novelty_score < 0.50:
                risks.append("기술 차별성 부족 — 독창성 추가 검토 필요")
            if market_analysis.commercial_feasibility_score < 12.5:
                risks.append("사업화 가능성 낮음 — 수익 모델 구체화 필요")
            if critical_gaps > 2:
                risks.append(f"주요 정보 공백 다수 존재 ({critical_gaps}건) — 추가 실사 필요")
            if competitor_analysis.competitive_advantage_score < 0.50:
                risks.append("경쟁 우위 취약 — 시장 포지셔닝 전략 재검토 필요")
            if not startup_qualified:
                risks.append("상위 3개 기업 투자 적격 기준 미달 — 상대적 경쟁력 열위")

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

            # Build rationale (한국어 초안 — LLM polish에서 고도화됨)
            rec_kr = {"invest": "투자 권고", "hold_for_review": "추가 검토 필요", "pass": "투자 비권고"}.get(
                recommendation_str, recommendation_str
            )
            strengths_summary = "; ".join(strengths[:2]) if strengths else "강점 정보 부족"
            risks_summary     = "; ".join(risks[:2])     if risks     else "리스크 정보 부족"
            decision.rationale = (
                f"{startup.name}은 종합 점수 {overall_score:.0%}, 신뢰도 {confidence:.0%} 기준으로 [{rec_kr}] 판정을 받았습니다. "
                f"주요 강점: {strengths_summary}. "
                f"주요 리스크: {risks_summary}."
            )

            self.log_info(f"Investment decision complete: {recommendation_str}")
            self.log_info(f"Overall Assessment Score: {overall_score:.2f}")
            self.log_info(f"Confidence: {confidence:.2f}")

            return decision

        finally:
            self.end_execution()
