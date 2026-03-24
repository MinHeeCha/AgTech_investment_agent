"""Orchestrator — thin wrapper around the LangGraph evaluation graph."""

import logging
from typing import Optional

from langgraph.types import Command

from rag import Retriever
from models import FullEvaluationResult
from app.graph import build_graph, EvaluationState


class AgentOrchestrator:
    """Runs the LangGraph evaluation workflow with HITL support."""

    def __init__(self, retriever: Optional[Retriever] = None, max_workers: int = 4):
        self.logger    = logging.getLogger("AgentOrchestrator")
        self.retriever = retriever or Retriever()
        self.graph     = build_graph(self.retriever, max_workers)

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

        # ── HITL 루프 ─────────────────────────────────────────────────
        while state.get("__interrupt__"):
            for iv in state["__interrupt__"]:
                print(iv.value)

            raw = input("입력 (approve / reanalyze): ").strip().lower()
            feedback = "reanalyze" if raw == "reanalyze" else "approve"

            state = self.graph.invoke(Command(resume=feedback), config)

        return state.get("final_results", [])

    def get_workflow_summary(self) -> dict:
        return {
            "stages": 4,
            "total_agents": 7,
            "parallel_agents": "N기업 × 4",
            "hitl": True,
            "workflow": [
                "Step 0: Startup Discovery  (벡터 DB → 기업 이름 리스트)",
                "Step 1: Parallel Analysis  (모든 기업 × 4 에이전트 동시 실행)",
                "[HITL] Human Review        (approve / reanalyze)",
                "Step 2–4: Downstream       (competitor → decision → report)",
            ],
        }
