"""Orchestrator — thin wrapper around the LangGraph evaluation graph."""

import logging
from typing import Optional, Any

from rag import Retriever
from models import FullEvaluationResult, StartupProfile
from app.graph import build_graph, EvaluationState
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
    """Runs the LangGraph evaluation workflow with HITL support."""

    def __init__(self, retriever: Optional[Retriever] = None, max_workers: int = 4):
        self.logger    = logging.getLogger("AgentOrchestrator")
        self.retriever = retriever or Retriever()
        self.graph     = build_graph(self.retriever, max_workers)

        # Keep explicit agent references for direct orchestration APIs.
        self.discovery_agent = StartupDiscoveryAgent()
        self.tech_agent = TechnologySummaryAgent()
        self.market_agent = MarketabilityEvaluationAgent()
        self.impact_agent = ImpactEvaluationAgent()
        self.moat_agent = DataMoatAnalysisAgent()
        self.competitor_agent = CompetitorComparisonAgent()
        self.decision_agent = InvestmentDecisionAgent()
        self.report_agent = ReportGenerationAgent()

    @staticmethod
    def _build_startup_profile(startup_name: str, startup_info: Optional[dict[str, Any]] = None) -> StartupProfile:
        """Create StartupProfile with sane defaults from input dict."""
        info = startup_info or {}
        return StartupProfile(
            name=startup_name,
            founded_year=info.get("founded_year", 0),
            headquarters=info.get("headquarters", "Unknown"),
            website=info.get("website"),
            description=info.get("description", ""),
            mission=info.get("mission"),
            founders=info.get("founders", []),
            industry=info.get("industry"),
            target_markets=info.get("target_markets", []),
            stage=info.get("stage"),
        )

    @staticmethod
    def _compute_step1_company_score(tech_analysis, market_analysis) -> float:
        """Compute a normalized Step 1 composite score in [0, 1]."""
        tech_score = (tech_analysis.novelty_score + tech_analysis.defensibility_score) / 2.0
        market_score = (
            market_analysis.market_growth_potential +
            market_analysis.commercial_feasibility_score
        ) / 2.0
        return max(0.0, min(1.0, (tech_score + market_score) / 2.0))

    def evaluate_startup(self, startup_name: str, startup_info: Optional[dict[str, Any]] = None) -> FullEvaluationResult:
        """
        Evaluate a single startup through step1 -> step4 pipeline.

        Uses one-company Step 1 score map for compatibility with step2 ranking input.
        """
        results = self.evaluate_multiple_startups([startup_name], {startup_name: startup_info or {}})
        return results[0]

    def evaluate_multiple_startups(
        self,
        startup_names: list[str],
        startup_infos: Optional[dict[str, dict[str, Any]]] = None
    ) -> list[FullEvaluationResult]:
        """
        Evaluate multiple startups with shared Step 1 scoring context.

        Step 1 runs for all companies first, then Step 2 receives a full
        company-score map so it can return top-3 by total score.
        """
        infos = startup_infos or {}
        profiles: dict[str, StartupProfile] = {
            name: self._build_startup_profile(name, infos.get(name)) for name in startup_names
        }

        # Step 1 (all companies first)
        tech_analyses = {}
        market_analyses = {}
        impact_analyses = {}
        moat_analyses = {}
        step1_company_scores = {}

        for name in startup_names:
            profile = profiles[name]
            tech = self.tech_agent.execute(profile, self.retriever)
            market = self.market_agent.execute(name, self.retriever)
            impact = self.impact_agent.execute(name, self.retriever)
            moat = self.moat_agent.execute(profile, self.retriever)

            tech_analyses[name] = tech
            market_analyses[name] = market
            impact_analyses[name] = impact
            moat_analyses[name] = moat
            step1_company_scores[name] = self._compute_step1_company_score(tech, market)

        # Step 2-4
        final_results: list[FullEvaluationResult] = []
        for name in startup_names:
            profile = profiles[name]
            tech = tech_analyses[name]
            market = market_analyses[name]
            impact = impact_analyses[name]
            moat = moat_analyses[name]

            competitor = self.competitor_agent.execute(
                profile,
                tech,
                market,
                self.retriever,
                step1_company_scores=step1_company_scores,
            )
            decision = self.decision_agent.execute(profile, tech, market, impact, moat, competitor)
            evaluation = self.report_agent.execute(profile, tech, market, impact, moat, competitor, decision)
            final_results.append(evaluation)

        return final_results

    def evaluate_all(self) -> list[FullEvaluationResult]:
        """
        Step 0으로 기업 목록을 발견하고 전체 평가 파이프라인을 실행한다.

        Step 1 완료 후 HITL로 일시정지 → 사용자가 approve / reanalyze 입력.

        Returns:
            List of FullEvaluationResult
        """
        config = {"configurable": {"thread_id": "evaluation_run"}}
        initial_state: EvaluationState = {
            "startup_names":      [],
            "tech_analyses":      {},
            "market_analyses":    {},
            "impact_analyses":    {},
            "moat_analyses":      {},
            "competitor_analyses":{},
            "investment_decisions":{},
            "final_results":      [],
            "human_feedback":     None,
            "reanalyze_targets":  [],
            "reanalysis_count":   0,
        }

        state = self.graph.invoke(initial_state, config)
        return state.get("final_results", [])

    def get_workflow_summary(self) -> dict:
        return {
            "stages": 5,
            "total_agents": 8,
            "parallel_agents": 4,
            "hitl": True,
            "workflow": [
                "Step 0: Startup Discovery  (벡터 DB → 기업 이름 리스트)",
                "Step 1: Parallel Analysis  (모든 기업 × 4 에이전트 동시 실행)",
                "[HITL] Human Review        (approve / reanalyze)",
                "Step 2: Competitor Comparison",
                "Step 3-5: Decision & Reporting",
            ],
        }
