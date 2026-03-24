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
        """FAISS에서 기업 기본 정보 조회 후 StartupProfile 생성."""
        import re
        STAGE_PATTERN = r'(Series [A-D]|Seed|Pre-Seed|Pre-Series A)'
        try:
            # 기본 정보 검색
            docs = retriever.retrieve(f"{name} founded year headquarters location Series", top_k=4)
            context = " ".join(d.content[:500] for d in docs)

            # 설립연도 추출
            years = re.findall(r'\b(20(?:1[0-9]|2[0-4]))\b', context)
            founded = int(years[0]) if years else 0

            # 본사 위치 — "Headquarters: City, Country" 패턴 우선 탐색
            HQ_BLACKLIST = {"Page", "Series", "The", "AgTech", "Seed", "Pre"}
            hq = "Unknown"
            hq_labeled = re.search(
                r'(?:Headquarters|HQ|Location|본사)[:\s]+([A-Za-z][A-Za-z\s]+(?:,\s*[A-Za-z]+)?)',
                context, re.IGNORECASE
            )
            if hq_labeled:
                hq = hq_labeled.group(1).strip()
            else:
                for m in re.finditer(r'([A-Z][a-z]{2,}(?:,\s*[A-Z][a-zA-Z]+)?)', context):
                    candidate = m.group(1).strip()
                    if candidate.split(",")[0].strip() not in HQ_BLACKLIST:
                        hq = candidate
                        break

            # 투자 단계 — 먼저 "{name} | Series X" 패턴으로 우선 탐색
            stage = None
            targeted = re.search(
                rf'{re.escape(name)}\s*[|\-–]\s*({STAGE_PATTERN[1:-1]})',
                context, re.IGNORECASE
            )
            if targeted:
                stage = targeted.group(1)
            else:
                stage_match = re.search(STAGE_PATTERN, context, re.IGNORECASE)
                stage = stage_match.group(1) if stage_match else None

            # stage를 못 찾았으면 전용 쿼리로 재검색
            if not stage:
                stage_docs = retriever.retrieve(f"{name} Series A Series B stage funding round", top_k=3)
                stage_context = " ".join(d.content[:600] for d in stage_docs)
                targeted2 = re.search(
                    rf'{re.escape(name)}\s*[|\-–]\s*({STAGE_PATTERN[1:-1]})',
                    stage_context, re.IGNORECASE
                )
                if targeted2:
                    stage = targeted2.group(1)
                else:
                    sm = re.search(STAGE_PATTERN, stage_context, re.IGNORECASE)
                    stage = sm.group(1) if sm else None
        except Exception:
            founded, hq, stage = 0, "Unknown", None
        return StartupProfile(name=name, founded_year=founded, headquarters=hq, stage=stage)

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
        """Step 2: top-3 선정 → Step 3: top-1 결정 → Step 4: report"""
        logger.info("[Step 2] Step 1 점수로 top-3 선정")

        # ── Step 1 composite score 계산 ──────────────────────────────
        step1_company_scores: dict[str, float] = {}
        for name in state["startup_names"]:
            tech   = state["tech_analyses"][name]
            market = state["market_analyses"][name]
            tech_score   = (tech.novelty_score + tech.defensibility_score) / 2.0
            market_score = (market.market_growth_potential / 11.0 + market.commercial_feasibility_score / 25.0) / 2.0
            step1_company_scores[name] = (tech_score + market_score) / 2.0

        # ── Step 2: top-3 선정 ───────────────────────────────────────
        sorted_companies = sorted(step1_company_scores.items(), key=lambda x: x[1], reverse=True)
        top3_names = [name for name, _ in sorted_companies[:3]]
        logger.info(f"[Step 2] Top-3: {top3_names}")

        # ── Step 3: top-3 각각 investment decision 실행 ──────────────
        logger.info("[Step 3] Top-3 기업 investment decision 실행")
        decisions: dict[str, Any] = {}
        competitors: dict[str, Any] = {}
        for name in top3_names:
            profile    = _profile(name)
            tech       = state["tech_analyses"][name]
            market     = state["market_analyses"][name]
            impact     = state["impact_analyses"][name]
            moat       = state["moat_analyses"][name]
            competitor = competitor_agent.execute(
                profile, tech, market, retriever,
                step1_company_scores=step1_company_scores,
            )
            decision = decision_agent.execute(profile, tech, market, impact, moat, competitor)
            decisions[name]   = decision
            competitors[name] = competitor
            logger.info(
                f"  {name}: score={decision.overall_assessment_score:.2f} "
                f"rec={decision.recommendation}"
            )

        # ── Top-1 or 전체 비권고 분기 ────────────────────────────────
        threshold = decision_agent.MIN_QUALIFIED_SCORE
        qualified = {n: d for n, d in decisions.items() if d.overall_assessment_score >= threshold}

        # ── Step 4: Report 생성 ───────────────────────────────────────
        logger.info("[Step 4] Report 생성")
        if qualified:
            # 임계값 통과 기업 중 최고점 → 단일 보고서
            top1_name = max(qualified, key=lambda n: qualified[n].overall_assessment_score)
            logger.info(f"[Step 3] Top-1 선정: {top1_name} (score={decisions[top1_name].overall_assessment_score:.2f})")
            report_targets = [top1_name]
        else:
            # 임계값 통과 기업 없음 → top-3 전체 투자 비권고 보고서
            logger.info("[Step 3] 임계값 통과 기업 없음 — top-3 전체 투자 비권고 보고서 생성")
            report_targets = top3_names

        evaluations = []
        for name in report_targets:
            evaluation = report_agent.execute(
                _profile(name),
                state["tech_analyses"][name],
                state["market_analyses"][name],
                state["impact_analyses"][name],
                state["moat_analyses"][name],
                competitors[name],
                decisions[name],
            )
            evaluations.append(evaluation)
            logger.info(f"  보고서 생성 완료: {name}")

        return {"final_results": evaluations}

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
