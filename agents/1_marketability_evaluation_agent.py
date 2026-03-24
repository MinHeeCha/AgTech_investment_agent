"""Marketability Evaluation Agent - Analyzes market potential."""

from typing import Optional
from models import MarketabilityAnalysisResult, EvidenceItem, StartupProfile
from rag import Retriever
from .base_agent import BaseAgent


class MarketabilityEvaluationAgent(BaseAgent):
    """Agent responsible for evaluating market potential and business model."""

    def __init__(self):
        super().__init__(
            name="MarketabilityEvaluationAgent",
            description="Evaluates target market, customer pain points, and commercial feasibility",
        )

    def execute(self, startup: StartupProfile,
               retriever: Optional[Retriever] = None) -> MarketabilityAnalysisResult:
        """
        Evaluate startup marketability.

        Args:
            startup: Startup profile to analyze
            retriever: Optional Retriever for market information

        Returns:
            MarketabilityAnalysisResult
        """
        self.start_execution()

        try:
            self.log_info(f"Evaluating marketability for {startup.name}")

            result = MarketabilityAnalysisResult(
                target_market_size="$50B+ global agricultural technology market",
                market_growth_potential=0.78,
                business_model="SaaS subscription and usage-based pricing",
                commercial_feasibility_score=0.70,
            )

            # Identify customer pain points
            result.customer_pain_points = [
                "Crop monitoring and early disease detection",
                "Optimization of irrigation and water usage",
                "Labor shortage for crop management",
                "Inconsistent yield prediction",
            ]

            # Identify adoption barriers
            result.adoption_barriers = [
                "Farmer technology adoption curve",
                "Integration with existing farm management systems",
                "Regulatory compliance in different regions",
            ]

            # Retrieve market information if retriever available
            if retriever:
                market_docs = self.retrieve_documents(
                    retriever,
                    f"{startup.name} market customers business model revenue agriculture",
                    top_k=5
                )

                # Create evidence from market documents
                for doc in market_docs[:3]:
                    evidence = EvidenceItem(
                        claim=f"Market information from {doc.source}",
                        source_document=doc.source,
                        evidence_type="market_data",
                        confidence=doc.relevance_score,
                        supporting_details=doc.content[:200] if doc.content else None
                    )
                    result.evidence.append(evidence)

            # Add missing information
            if not result.target_market_size:
                result.missing_information.append("TAM sizing information not found")

            result.summary = f"Market Growth Potential: {result.market_growth_potential:.2f}. " \
                           f"Commercial Feasibility: {result.commercial_feasibility_score:.2f}. " \
                           f"Business Model: {result.business_model}."

            self.log_info(f"Marketability analysis complete for {startup.name}")

            return result

        finally:
            self.end_execution()
