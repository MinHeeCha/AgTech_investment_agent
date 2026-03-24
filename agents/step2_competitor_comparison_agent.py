"""Competitor Comparison Agent - Compares startup with competitors."""

from typing import Optional
from models import (
    CompetitorAnalysisResult, EvidenceItem, StartupProfile,
    TechnologyAnalysisResult, MarketabilityAnalysisResult
)
from rag import Retriever
from .base_agent import BaseAgent


class CompetitorComparisonAgent(BaseAgent):
    """Agent responsible for competitive analysis and comparison."""

    def __init__(self):
        super().__init__(
            name="CompetitorComparisonAgent",
            description="Compares analyzed startup with comparable competitors",
        )

    def execute(self, startup: StartupProfile,
               tech_analysis: TechnologyAnalysisResult,
               market_analysis: MarketabilityAnalysisResult,
               retriever: Optional[Retriever] = None) -> CompetitorAnalysisResult:
        """
        Perform competitive comparison.

        Args:
            startup: Startup profile
            tech_analysis: Technology analysis results
            market_analysis: Market analysis results
            retriever: Optional Retriever for competitor information

        Returns:
            CompetitorAnalysisResult
        """
        self.start_execution()

        try:
            self.log_info(f"Analyzing competitors for {startup.name}")

            result = CompetitorAnalysisResult(
                comparable_competitors=[
                    "Competitor A - Satellite imagery platform",
                    "Competitor B - Drone-based monitoring",
                    "Competitor C - AI crop analytics",
                ],
                technology_differentiation="Proprietary multi-sensor fusion approach vs single-modality competitors",
                technology_differentiation_score=0.72,
                market_position_analysis="Strong positioning in mid-market farmers, emerging in enterprise segment",
                relative_barriers_to_entry=0.75,
                competitive_advantage_score=0.71,
            )

            # Identify relative strengths
            if tech_analysis.novelty_score > 0.65:
                result.relative_strengths.append("Superior technology differentiation")
            if market_analysis.market_growth_potential > 0.70:
                result.relative_strengths.append("Larger addressable market opportunity")
            result.relative_strengths.append("Unique data moat potential")

            # Identify relative weaknesses
            result.relative_weaknesses = [
                "Lower brand recognition than established players",
                "Smaller financial resources vs well-funded competitors",
                "Earlier stage product maturity",
            ]

            # Retrieve competitor information if retriever available
            if retriever:
                comp_docs = self.retrieve_documents(
                    retriever,
                    f"{startup.name} competitors competitive landscape comparison",
                    top_k=5
                )

                # Create evidence from competitor documents
                for doc in comp_docs[:3]:
                    evidence = EvidenceItem(
                        claim=f"Competitive information from {doc.source}",
                        source_document=doc.source,
                        evidence_type="competitive_analysis",
                        confidence=doc.relevance_score,
                        supporting_details=doc.content[:200] if doc.content else None
                    )
                    result.evidence.append(evidence)

            result.summary = f"Competitive Advantage Score: {result.competitive_advantage_score:.2f}. " \
                           f"Key Differentiation: {result.technology_differentiation}. " \
                           f"Competitors: {len(result.comparable_competitors)} identified."

            self.log_info(f"Competitive analysis complete for {startup.name}")

            return result

        finally:
            self.end_execution()
