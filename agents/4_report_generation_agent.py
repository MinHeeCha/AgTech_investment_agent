"""Report Generation Agent - Creates final evaluation report."""

from typing import Optional
from datetime import datetime
from models import (
    FullEvaluationResult, StartupProfile,
    TechnologyAnalysisResult, MarketabilityAnalysisResult, ImpactAnalysisResult,
    DataMoatAnalysisResult, CompetitorAnalysisResult, InvestmentDecision
)
from .base_agent import BaseAgent


class ReportGenerationAgent(BaseAgent):
    """Agent responsible for generating the final evaluation report."""

    def __init__(self):
        super().__init__(
            name="ReportGenerationAgent",
            description="Generates structured evaluation report",
        )

    def execute(self,
               startup: StartupProfile,
               tech_analysis: TechnologyAnalysisResult,
               market_analysis: MarketabilityAnalysisResult,
               impact_analysis: ImpactAnalysisResult,
               data_moat_analysis: DataMoatAnalysisResult,
               competitor_analysis: CompetitorAnalysisResult,
               investment_decision: InvestmentDecision) -> FullEvaluationResult:
        """
        Generate final evaluation report.

        Args:
            startup: Startup profile
            tech_analysis: Technology analysis results
            market_analysis: Market analysis results
            impact_analysis: Impact analysis results
            data_moat_analysis: Data moat analysis results
            competitor_analysis: Competitor analysis results
            investment_decision: Investment decision

        Returns:
            FullEvaluationResult with complete report
        """
        self.start_execution()

        try:
            self.log_info(f"Generating report for {startup.name}")

            # Create evaluation result
            evaluation = FullEvaluationResult(
                startup=startup,
                technology_analysis=tech_analysis,
                marketability_analysis=market_analysis,
                impact_analysis=impact_analysis,
                data_moat_analysis=data_moat_analysis,
                competitor_analysis=competitor_analysis,
                investment_decision=investment_decision,
            )

            # Generate comprehensive report content
            report_content = self._generate_report_content(evaluation)
            evaluation.report_content = report_content

            self.log_info(f"Report generation complete for {startup.name}")

            return evaluation

        finally:
            self.end_execution()

    def _generate_report_content(self, evaluation: FullEvaluationResult) -> str:
        """Generate detailed report text."""
        report = []

        # Header
        report.append("=" * 80)
        report.append("AGTECH STARTUP INVESTMENT EVALUATION REPORT")
        report.append("=" * 80)
        report.append("")

        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 80)
        report.append(f"Company: {evaluation.startup.name}")
        report.append(f"Founded: {evaluation.startup.founded_year}")
        report.append(f"Stage: {evaluation.startup.stage}")
        report.append(f"Headquarters: {evaluation.startup.headquarters}")
        report.append("")
        report.append(f"INVESTMENT RECOMMENDATION: {evaluation.investment_decision.recommendation.value.upper()}")
        report.append(f"Overall Assessment Score: {evaluation.investment_decision.overall_assessment_score:.2%}")
        report.append(f"Confidence Level: {evaluation.investment_decision.confidence_score:.2%}")
        report.append("")
        report.append(f"Rationale:\n{evaluation.investment_decision.rationale}")
        report.append("")

        # Detailed Analysis
        report.append("DETAILED ANALYSIS")
        report.append("-" * 80)

        # Technology Analysis
        report.append("\n1. TECHNOLOGY ANALYSIS")
        report.append(f"   Core Technology: {evaluation.technology_analysis.core_technology}")
        report.append(f"   Novelty Score: {evaluation.technology_analysis.novelty_score:.2%}")
        report.append(f"   Defensibility Score: {evaluation.technology_analysis.defensibility_score:.2%}")
        if evaluation.technology_analysis.patents:
            report.append(f"   Patents: {', '.join(evaluation.technology_analysis.patents)}")
        report.append(f"   Technical Keywords: {', '.join(evaluation.technology_analysis.technical_keywords)}")
        report.append(f"   Summary: {evaluation.technology_analysis.summary}")

        # Market Analysis
        report.append("\n2. MARKET ANALYSIS")
        report.append(f"   Target Market: {evaluation.marketability_analysis.target_market_size}")
        report.append(f"   Market Growth Potential: {evaluation.marketability_analysis.market_growth_potential:.2%}")
        report.append(f"   Commercial Feasibility: {evaluation.marketability_analysis.commercial_feasibility_score:.2%}")
        report.append(f"   Business Model: {evaluation.marketability_analysis.business_model}")
        report.append(f"   Customer Pain Points: {', '.join(evaluation.marketability_analysis.customer_pain_points)}")
        report.append(f"   Summary: {evaluation.marketability_analysis.summary}")

        # Impact Analysis
        report.append("\n3. IMPACT ANALYSIS")
        report.append(f"   Environmental Impact: {evaluation.impact_analysis.environmental_impact:.2%}")
        report.append(f"   Agricultural Impact: {evaluation.impact_analysis.agricultural_impact:.2%}")
        report.append(f"   Sustainability Focus: {', '.join(evaluation.impact_analysis.sustainability_focus)}")
        if evaluation.impact_analysis.yield_improvement_claimed:
            report.append(f"   Yield Improvement: {evaluation.impact_analysis.yield_improvement_claimed}")
        if evaluation.impact_analysis.water_saving_claimed:
            report.append(f"   Water Savings: {evaluation.impact_analysis.water_saving_claimed}")
        report.append(f"   Summary: {evaluation.impact_analysis.summary}")

        # Data Moat Analysis
        report.append("\n4. DATA MOAT ANALYSIS")
        report.append(f"   Moat Strength Score: {evaluation.data_moat_analysis.moat_strength_score:.2%}")
        report.append(f"   Proprietary Datasets: {evaluation.data_moat_analysis.has_proprietary_datasets}")
        report.append(f"   Data Defensibility: {evaluation.data_moat_analysis.dataset_defensibility_score:.2%}")
        report.append(f"   Flywheel Potential: {evaluation.data_moat_analysis.data_flywheel_potential:.2%}")
        report.append(f"   Summary: {evaluation.data_moat_analysis.summary}")

        # Competitive Analysis
        report.append("\n5. COMPETITIVE ANALYSIS")
        report.append(f"   Competitive Advantage Score: {evaluation.competitor_analysis.competitive_advantage_score:.2%}")
        report.append(f"   Identified Competitors: {', '.join(evaluation.competitor_analysis.comparable_competitors)}")
        report.append(f"   Technology Differentiation: {evaluation.competitor_analysis.technology_differentiation}")
        report.append(f"   Strengths: {', '.join(evaluation.competitor_analysis.relative_strengths)}")
        report.append(f"   Weaknesses: {', '.join(evaluation.competitor_analysis.relative_weaknesses)}")
        report.append(f"   Summary: {evaluation.competitor_analysis.summary}")

        # Investment Decision
        report.append("\n6. INVESTMENT DECISION")
        report.append(f"   Recommendation: {evaluation.investment_decision.recommendation.value.upper()}")
        report.append(f"   Overall Score: {evaluation.investment_decision.overall_assessment_score:.2%}")
        report.append(f"   Confidence: {evaluation.investment_decision.confidence_score:.2%}")
        report.append(f"   Key Strengths:")
        for strength in evaluation.investment_decision.key_strengths:
            report.append(f"      • {strength}")
        report.append(f"   Key Risks:")
        for risk in evaluation.investment_decision.key_risks:
            report.append(f"      • {risk}")

        # Evidence Gaps
        if evaluation.investment_decision.evidence_gaps:
            report.append(f"\n   Evidence Gaps:")
            for gap in evaluation.investment_decision.evidence_gaps[:5]:
                report.append(f"      • {gap}")

        # Conclusion
        report.append("\n" + "=" * 80)
        report.append(f"Report Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, evaluation: FullEvaluationResult, filepath: str):
        """
        Save report to file.

        Args:
            evaluation: Evaluation result with report content
            filepath: Path to save report
        """
        try:
            with open(filepath, "w") as f:
                f.write(evaluation.report_content)
            self.log_info(f"Report saved to {filepath}")
        except Exception as e:
            self.log_error(f"Failed to save report: {e}")
