"""Orchestrator for managing the multi-agent workflow."""

import asyncio
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from rag import Retriever
from models import StartupProfile, FullEvaluationResult
from agents import (
    StartupDiscoveryAgent,
    TechnologySummaryAgent,
    MarketabilityEvaluationAgent,
    ImpactEvaluationAgent,
    DataMoatAnalysisAgent,
    CompetitorComparisonAgent,
    InvestmentDecisionAgent,
    ReportGenerationAgent,
)


class AgentOrchestrator:
    """Orchestrates the multi-agent investment evaluation workflow."""

    def __init__(self, retriever: Optional[Retriever] = None, max_workers: int = 4):
        """
        Initialize the orchestrator.

        Args:
            retriever: Optional Retriever instance for RAG
            max_workers: Maximum number of parallel workers
        """
        self.logger = logging.getLogger("AgentOrchestrator")
        self.retriever = retriever or Retriever()
        self.max_workers = max_workers

        # Initialize all agents
        self.discovery_agent = StartupDiscoveryAgent()
        self.tech_agent = TechnologySummaryAgent()
        self.market_agent = MarketabilityEvaluationAgent()
        self.impact_agent = ImpactEvaluationAgent()
        self.data_moat_agent = DataMoatAnalysisAgent()
        self.competitor_agent = CompetitorComparisonAgent()
        self.decision_agent = InvestmentDecisionAgent()
        self.report_agent = ReportGenerationAgent()

    def evaluate_startup(self, startup_name: str,
                        startup_info: Optional[dict] = None) -> FullEvaluationResult:
        """
        Perform complete startup evaluation through the multi-agent pipeline.

        Workflow:
        1. StartupDiscoveryAgent: Profile the startup
        2. Parallel execution of 4 analysis agents:
           - TechnologySummaryAgent
           - MarketabilityEvaluationAgent
           - ImpactEvaluationAgent
           - DataMoatAnalysisAgent
        3. CompetitorComparisonAgent: Compare with competitors
        4. InvestmentDecisionAgent: Make investment decision
        5. ReportGenerationAgent: Generate final report

        Args:
            startup_name: Name of the startup to evaluate
            startup_info: Optional additional startup information

        Returns:
            FullEvaluationResult with complete evaluation
        """
        self.logger.info(f"Starting evaluation pipeline for {startup_name}")

        # Step 1: Startup Discovery
        self.logger.info("Step 1: Startup Discovery")
        startup = self.discovery_agent.execute(startup_name, self.retriever, startup_info)
        self.logger.info(f"Discovered startup: {startup}")

        # Step 2: Parallel analysis
        self.logger.info("Step 2: Parallel Analysis Agents (Technology, Market, Impact, Data Moat)")
        with ThreadPoolExecutor(max_workers=min(4, self.max_workers)) as executor:
            tech_future = executor.submit(
                self.tech_agent.execute, startup, self.retriever
            )
            market_future = executor.submit(
                self.market_agent.execute, startup, self.retriever
            )
            impact_future = executor.submit(
                self.impact_agent.execute, startup, self.retriever
            )
            data_moat_future = executor.submit(
                self.data_moat_agent.execute, startup, self.retriever
            )

            tech_analysis = tech_future.result()
            market_analysis = market_future.result()
            impact_analysis = impact_future.result()
            data_moat_analysis = data_moat_future.result()

        self.logger.info("Parallel analysis complete")

        # Step 3: Competitor Comparison
        self.logger.info("Step 3: Competitor Comparison")
        competitor_analysis = self.competitor_agent.execute(
            startup, tech_analysis, market_analysis, self.retriever
        )
        self.logger.info("Competitor analysis complete")

        # Step 4: Investment Decision
        self.logger.info("Step 4: Investment Decision")
        investment_decision = self.decision_agent.execute(
            startup, tech_analysis, market_analysis, impact_analysis,
            data_moat_analysis, competitor_analysis
        )
        self.logger.info(f"Decision: {investment_decision.recommendation}")

        # Step 5: Report Generation
        self.logger.info("Step 5: Report Generation")
        evaluation = self.report_agent.execute(
            startup, tech_analysis, market_analysis, impact_analysis,
            data_moat_analysis, competitor_analysis, investment_decision
        )

        self.logger.info(f"Evaluation complete for {startup_name}")

        return evaluation

    def evaluate_multiple_startups(self, startup_names: list[str],
                                  startup_infos: Optional[dict] = None) -> list[FullEvaluationResult]:
        """
        Evaluate multiple startups sequentially.

        Args:
            startup_names: List of startup names
            startup_infos: Optional dict of startup_name -> startup_info

        Returns:
            List of evaluation results
        """
        if startup_infos is None:
            startup_infos = {}

        results = []
        for i, name in enumerate(startup_names, 1):
            self.logger.info(f"Evaluating startup {i}/{len(startup_names)}: {name}")
            info = startup_infos.get(name)
            result = self.evaluate_startup(name, info)
            results.append(result)

        self.logger.info(f"Batch evaluation complete: {len(results)} startups evaluated")
        return results

    def get_workflow_summary(self) -> dict:
        """Get summary of the workflow."""
        return {
            "stages": 5,
            "total_agents": 8,
            "parallel_agents": 4,
            "workflow": [
                "Stage 1: Startup Discovery",
                "Stage 2: Parallel Analysis (4 agents)",
                "Stage 3: Competitor Comparison",
                "Stage 4: Investment Decision",
                "Stage 5: Report Generation",
            ],
        }
