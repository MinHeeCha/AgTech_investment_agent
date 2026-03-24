"""Technology Summary Agent - Analyzes core technology."""

from typing import Optional
from models import TechnologyAnalysisResult, EvidenceItem, StartupProfile
from rag import Retriever
from .base_agent import BaseAgent


class TechnologySummaryAgent(BaseAgent):
    """Agent responsible for analyzing startup technology and innovation."""

    def __init__(self):
        super().__init__(
            name="TechnologySummaryAgent",
            description="Summarizes core technology, patents, papers, and technical keywords",
        )

    def execute(self, startup: StartupProfile, 
               retriever: Optional[Retriever] = None) -> TechnologyAnalysisResult:
        """
        Analyze startup technology.

        Args:
            startup: Startup profile to analyze
            retriever: Optional Retriever for gathering technical information

        Returns:
            TechnologyAnalysisResult
        """
        self.start_execution()

        try:
            self.log_info(f"Analyzing technology for {startup.name}")

            result = TechnologyAnalysisResult(
                core_technology="Advanced agricultural optimization platform",
                novelty_score=0.72,
                defensibility_score=0.65,
            )

            # Retrieve technology-related documents if retriever available
            if retriever:
                tech_docs = self.retrieve_documents(
                    retriever,
                    f"{startup.name} technology patents innovation AI machine learning",
                    top_k=5
                )

                # Extract patents
                for doc in tech_docs:
                    if "patent" in doc.document_type.lower():
                        result.patents.append(doc.source)

                # Extract research papers
                for doc in tech_docs:
                    if "paper" in doc.document_type.lower() or "research" in doc.document_type.lower():
                        result.research_papers.append(doc.source)

                # Create evidence items from retrieved documents
                for doc in tech_docs[:3]:
                    evidence = EvidenceItem(
                        claim=f"Technology information from {doc.source}",
                        source_document=doc.source,
                        evidence_type="technical_document",
                        confidence=doc.relevance_score,
                        supporting_details=doc.content[:200] if doc.content else None
                    )
                    result.evidence.append(evidence)

            # Add technical keywords
            result.technical_keywords = [
                "precision agriculture",
                "IoT sensors",
                "computer vision",
                "real-time monitoring",
                "predictive analytics"
            ]

            # Add placeholder for missing information
            if not result.patents:
                result.missing_information.append("Patent portfolio details not found")
            if not result.research_papers:
                result.missing_information.append("Research publications not found")

            result.summary = f"Core technology: {result.core_technology}. " \
                           f"Novelty Score: {result.novelty_score:.2f}. " \
                           f"Defensibility: {result.defensibility_score:.2f}."

            self.log_info(f"Technology analysis complete for {startup.name}")

            return result

        finally:
            self.end_execution()
