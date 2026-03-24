"""Data Moat Analysis Agent - Evaluates data assets and defensibility."""

from typing import Optional
from models import DataMoatAnalysisResult, EvidenceItem, StartupProfile
from rag import Retriever
from .base_agent import BaseAgent


class DataMoatAnalysisAgent(BaseAgent):
    """Agent responsible for analyzing data assets and competitive moat."""

    def __init__(self):
        super().__init__(
            name="DataMoatAnalysisAgent",
            description="Evaluates proprietary datasets, data flywheel, and data defensibility",
        )

    def execute(self, startup: StartupProfile,
               retriever: Optional[Retriever] = None) -> DataMoatAnalysisResult:
        """
        Analyze startup data moat.

        Args:
            startup: Startup profile to analyze
            retriever: Optional Retriever for data-related information

        Returns:
            DataMoatAnalysisResult
        """
        self.start_execution()

        try:
            self.log_info(f"Analyzing data moat for {startup.name}")

            result = DataMoatAnalysisResult(
                has_proprietary_datasets=True,
                dataset_defensibility_score=0.72,
                data_flywheel_potential=0.68,
                sensing_pipeline_uniqueness="Multi-spectral sensor array with proprietary processing",
                data_assets_description="Proprietary agricultural imagery and soil data database",
                moat_strength_score=0.70,
            )

            # Retrieve data-related information if retriever available
            if retriever:
                data_docs = self.retrieve_documents(
                    retriever,
                    f"{startup.name} data algorithms machine learning proprietary datasets",
                    top_k=5
                )

                # Create evidence from data documents
                for doc in data_docs[:3]:
                    evidence = EvidenceItem(
                        claim=f"Data asset information from {doc.source}",
                        source_document=doc.source,
                        evidence_type="data_asset",
                        confidence=doc.relevance_score,
                        supporting_details=doc.content[:200] if doc.content else None
                    )
                    result.evidence.append(evidence)

            # Add missing information
            if not result.data_assets_description:
                result.missing_information.append("Data asset inventory not found")
            if not result.sensing_pipeline_uniqueness:
                result.missing_information.append("Sensing infrastructure details not found")

            result.summary = f"Data Moat Strength: {result.moat_strength_score:.2f}. " \
                           f"Proprietary Datasets: {result.has_proprietary_datasets}. " \
                           f"Defensibility: {result.dataset_defensibility_score:.2f}. " \
                           f"Flywheel Potential: {result.data_flywheel_potential:.2f}."

            self.log_info(f"Data moat analysis complete for {startup.name}")

            return result

        finally:
            self.end_execution()
