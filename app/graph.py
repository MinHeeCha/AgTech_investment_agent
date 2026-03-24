"""LangGraph-based evaluation workflow with HITL support."""

import logging
from typing import Optional, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

from rag import Retriever
from models import StartupProfile
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

AGENT_KEYS = {"tech", "market", "impact", "moat"}


class EvaluationState(TypedDict):
    """Shared state passed between graph nodes."""

    # Step 0
    startup_names: list[str]

    # Step 1: 기업별 분석 결과 {startup_name: result}
    tech_analyses:   dict[str, Any]
    market_analyses: dict[str, Any]
    impact_analyses: dict[str, Any]
    moat_analyses:   dict[str, Any]

    # Step 2–4
    final_results: list[Any]

    # HITL
    human_feedback:    Optional[str]
    reanalyze_targets: list[str]   # "tech" | "market" | "impact" | "moat"
    reanalysis_count:  int


def build_graph(retriever: Retriever, max_workers: int = 4):
    logger = logging.getLogger("EvaluationGraph")

    discovery_agent  = StartupDiscoveryAgent()
    tech_agent       = TechnologySummaryAgent()
    market_agent     = MarketabilityEvaluationAgent()
    impact_agent     = ImpactEvaluationAgent()
    moat_agent       = DataMoatAnalysisAgent()
    competitor_agent = CompetitorComparisonAgent()
    decision_agent   = InvestmentDecisionAgent()
    report_agent     = ReportGenerationAgent()

    # ── 헬퍼 ──────────────────────────────────────────────────────────

    def _profile(name: str) -> StartupProfile:
        return StartupProfile(name=name, founded_year=0, headquarters="Unknown")

    # ── Step 0 ────────────────────────────────────────────────────────

    def node_discovery(state: EvaluationState) -> dict:
        logger.info("[Step 0] Discovery")
        names = discovery_agent.execute(retriever)
        logger.info(f"Discovered {len(names)} startups")
        print(f"\n{'='*60}")
        print(f"  Step 0 완료 — {len(names)}개 기업 발견")
        print(f"{'='*60}")
        for i, name in enumerate(names, 1):
            print(f"  {i:2d}. {name}")
        print(f"{'='*60}\n")
        return {"startup_names": names}

    # ── Step 1: 에이전트별 독립 노드 (각각 모든 기업을 처리) ───────────

    def node_tech(state: EvaluationState) -> dict:
        names = state["startup_names"]
        logger.info(f"[Step 1 / tech] {len(names)}개 기업")
        results = dict(state.get("tech_analyses") or {})
        for name in names:
            results[name] = tech_agent.execute(_profile(name), retriever)
        return {"tech_analyses": results}

    def node_market(state: EvaluationState) -> dict:
        names = state["startup_names"]
        logger.info(f"[Step 1 / market] {len(names)}개 기업")
        results = dict(state.get("market_analyses") or {})
        for name in names:
            results[name] = market_agent.execute(name, retriever)
        return {"market_analyses": results}

    def node_impact(state: EvaluationState) -> dict:
        names = state["startup_names"]
        logger.info(f"[Step 1 / impact] {len(names)}개 기업")
        results = dict(state.get("impact_analyses") or {})
        for name in names:
            results[name] = impact_agent.execute(name, retriever)
        return {"impact_analyses": results}

    def node_moat(state: EvaluationState) -> dict:
        names = state["startup_names"]
        logger.info(f"[Step 1 / moat] {len(names)}개 기업")
        results = dict(state.get("moat_analyses") or {})
        for name in names:
            results[name] = moat_agent.execute(name, retriever)
        return {"moat_analyses": results}

    # ── HITL (비활성화) ───────────────────────────────────────────────

    # def node_human_review(state: EvaluationState) -> Command:
    #     count = state.get("reanalysis_count", 0)
    #     lines = [
    #         f"\n{'='*60}",
    #         f"  [HITL] Step 1 결과 — {len(state['startup_names'])}개 기업",
    #         f"{'='*60}",
    #     ]
    #     for name in state["startup_names"]:
    #         impact = (state.get("impact_analyses") or {}).get(name)
    #         score  = f"{impact.total_impact_score:2d}/15" if impact else "  N/A"
    #         lines.append(f"  {name:20s}  임팩트 {score}")
    #     if count > 0:
    #         lines.append(f"\n  (재분석 {count}회 완료)")
    #     lines += [
    #         f"{'='*60}",
    #         "  approve  |  reanalyze [tech] [market] [impact] [moat]",
    #     ]
    #     feedback: str = interrupt("\n".join(lines))
    #     parts   = feedback.strip().lower().split()
    #     action  = parts[0] if parts else "approve"
    #     targets = [p for p in parts[1:] if p in AGENT_KEYS] or list(AGENT_KEYS)
    #     if action == "reanalyze":
    #         return Command(
    #             goto="node_reanalysis_dispatch",
    #             update={
    #                 "human_feedback":    feedback,
    #                 "reanalyze_targets": targets,
    #                 "reanalysis_count":  count + 1,
    #             },
    #         )
    #     return Command(
    #         goto="node_downstream",
    #         update={"human_feedback": feedback, "reanalyze_targets": []},
    #     )

    # def node_reanalysis_dispatch(state: EvaluationState) -> list[Send]:
    #     targets = state.get("reanalyze_targets") or list(AGENT_KEYS)
    #     logger.info(f"[Reanalysis] 재실행 대상: {targets}")
    #     return [Send(f"node_{t}", state) for t in targets]

    # ── Step 2–4 ──────────────────────────────────────────────────────

    def node_downstream(state: EvaluationState) -> dict:
        """기업별로 competitor → decision → report 순차 실행."""
        logger.info("[Step 2–4] Downstream pipeline")
        results = []
        step1_company_scores: dict[str, float] = {}

        # Build Step 1 composite score for each company.
        # This score is used by step2 to select top-3 competitors.
        for company_name in state["startup_names"]:
            tech_result = state["tech_analyses"][company_name]
            market_result = state["market_analyses"][company_name]
            tech_score = (
                tech_result.novelty_score + tech_result.defensibility_score
            ) / 2.0
            market_score = (
                market_result.market_growth_potential + market_result.commercial_feasibility_score
            ) / 2.0
            step1_company_scores[company_name] = (tech_score + market_score) / 2.0

        for name in state["startup_names"]:
            profile = _profile(name)
            tech    = state["tech_analyses"][name]
            market  = state["market_analyses"][name]
            impact  = state["impact_analyses"][name]
            moat    = state["moat_analyses"][name]

            competitor = competitor_agent.execute(
                profile,
                tech,
                market,
                retriever,
                step1_company_scores=step1_company_scores,
            )
            decision   = decision_agent.execute(profile, tech, market, impact, moat, competitor)
            evaluation = report_agent.execute(profile, tech, market, impact, moat, competitor, decision)
            results.append(evaluation)
            logger.info(f"  {name}: {decision.recommendation}")

        return {"final_results": results}

    # ── 그래프 조립 ───────────────────────────────────────────────────

    graph = StateGraph(EvaluationState)

    graph.add_node("node_discovery",  node_discovery)
    graph.add_node("node_tech",       node_tech)
    graph.add_node("node_market",     node_market)
    graph.add_node("node_impact",     node_impact)
    graph.add_node("node_moat",       node_moat)
    graph.add_node("node_downstream", node_downstream)

    # Step 0 → Step 1 fan-out
    graph.set_entry_point("node_discovery")
    for agent in AGENT_KEYS:
        graph.add_edge("node_discovery", f"node_{agent}")

    # Step 1 → downstream fan-in
    for agent in AGENT_KEYS:
        graph.add_edge(f"node_{agent}", "node_downstream")

    graph.add_edge("node_downstream", END)

    return graph.compile(checkpointer=MemorySaver())
