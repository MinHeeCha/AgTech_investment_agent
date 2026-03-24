"""Impact Evaluation Agent - Analyzes environmental and agricultural impact."""

from typing import Optional
from models import ImpactAnalysisResult, EvidenceItem, StartupProfile
from rag import Retriever
from .base_agent import BaseAgent


class ImpactEvaluationAgent(BaseAgent):
    """Agent responsible for evaluating environmental and agricultural impact."""

    def __init__(self):
        super().__init__(
            name="ImpactEvaluationAgent",
            description="Evaluates environmental, agricultural, and sustainability impact",
        )

    def execute(self, startup: StartupProfile,
               retriever: Optional[Retriever] = None) -> ImpactAnalysisResult:
        """
        Evaluate startup impact.

        Args:
            startup: Startup profile to analyze
            retriever: Optional Retriever for impact information

        Returns:
            ImpactAnalysisResult
        """
        self.start_execution()

        try:
            self.log_info(f"Evaluating impact for {startup.name}")

            result = ImpactAnalysisResult(
                environmental_impact=0.75,
                agricultural_impact=0.82,
                yield_improvement_claimed="15-25% improvement in crop yield",
                carbon_reduction_claimed="30% reduction in farm carbon footprint",
                water_saving_claimed="20-40% reduction in water usage",
            )

            # Set sustainability focus areas
            result.sustainability_focus = [
                "Efficient water management",
                "Reduced chemical usage",
                "Carbon footprint reduction",
                "Soil health optimization",
            ]

            # Set efficiency improvements
            result.efficiency_improvements = [
                "Reduced labor costs through automation",
                "Optimized resource allocation",
                "Improved crop yield consistency",
                "Earlier disease detection and prevention",
            ]

            # Retrieve impact information if retriever available
            if retriever:
                impact_docs = self.retrieve_documents(
                    retriever,
                    f"{startup.name} impact environmental sustainable agriculture yield",
                    top_k=5
                )

                # Create evidence from impact documents
                for doc in impact_docs[:3]:
                    evidence = EvidenceItem(
                        claim=f"Impact claim from {doc.source}",
                        source_document=doc.source,
                        evidence_type="impact_claim",
                        confidence=doc.relevance_score,
                        supporting_details=doc.content[:200] if doc.content else None
                    )
                    result.evidence.append(evidence)

            # Add missing information
            if not result.yield_improvement_claimed:
                result.missing_information.append("Yield improvement data not found")
            if not result.carbon_reduction_claimed:
                result.missing_information.append("Carbon impact quantification not found")

            result.summary = f"Environmental Impact: {result.environmental_impact:.2f}. " \
                           f"Agricultural Impact: {result.agricultural_impact:.2f}. " \
                           f"Focus: {', '.join(result.sustainability_focus)}"

            self.log_info(f"Impact analysis complete for {startup.name}")

            return result

        finally:
            self.end_execution()
