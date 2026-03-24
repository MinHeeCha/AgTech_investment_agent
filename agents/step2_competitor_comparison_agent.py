"""Competitor Comparison Agent - Selects top competitors from Step 1 scores."""

from typing import Any, Optional
from models import (
    CompetitorAnalysisResult,
    StartupProfile,
    TechnologyAnalysisResult,
    MarketabilityAnalysisResult,
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

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        """Clamp score into [minimum, maximum]."""
        return max(minimum, min(maximum, value))

    @staticmethod
    def _extract_score(payload: Any) -> Optional[float]:
        """Extract score from multiple Step 1 payload formats."""
        if isinstance(payload, (int, float)):
            return float(payload)
        if not isinstance(payload, dict):
            return None

        for key in ("total_score", "overall_score", "score"):
            value = payload.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return None

    @classmethod
    def _normalize_step1_scores(
        cls,
        step1_company_scores: Optional[Any]
    ) -> list[tuple[str, float]]:
        """
        Normalize Step 1 companies + scores to [(company_name, score)].

        Supported formats:
        - {"A": 0.78, "B": 0.66}
        - {"A": {"total_score": 0.78}, "B": {"score": 0.66}}
        - [{"name": "A", "total_score": 0.78}, ...]
        """
        normalized: list[tuple[str, float]] = []

        if isinstance(step1_company_scores, dict):
            for company_name, payload in step1_company_scores.items():
                score = cls._extract_score(payload)
                if score is not None:
                    normalized.append((str(company_name), score))
            return normalized

        if isinstance(step1_company_scores, list):
            for item in step1_company_scores:
                if not isinstance(item, dict):
                    continue
                name = item.get("name") or item.get("company") or item.get("company_name")
                if not name:
                    continue
                score = cls._extract_score(item)
                if score is not None:
                    normalized.append((str(name), score))

        return normalized

    @classmethod
    def _select_top_3_companies(
        cls,
        startup_name: str,
        startup_fallback_score: float,
        step1_company_scores: Optional[Any]
    ) -> tuple[list[str], list[tuple[str, float]], bool]:
        """Return top-3 company names from Step 1 scores."""
        scores = cls._normalize_step1_scores(step1_company_scores)
        used_step1_scores = len(scores) > 0

        # Ensure current startup exists in ranking, even if Step 1 payload omits it.
        existing_names = {name for name, _ in scores}
        if startup_name not in existing_names:
            scores.append((startup_name, startup_fallback_score))

        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
        top_3 = [name for name, _ in sorted_scores[:3]]
        return top_3, sorted_scores, used_step1_scores

    def execute(
        self,
        startup: StartupProfile,
        tech_analysis: TechnologyAnalysisResult,
        market_analysis: MarketabilityAnalysisResult,
        retriever: Optional[Retriever] = None,
        step1_company_scores: Optional[Any] = None
    ) -> CompetitorAnalysisResult:
        """
        Perform competitive comparison from Step 1 score ranking.

        Args:
            startup: Startup profile
            tech_analysis: Technology analysis results
            market_analysis: Market analysis results
            retriever: Kept for backward compatibility (not used)
            step1_company_scores: Step 1 company score data used for top-3 selection

        Returns:
            CompetitorAnalysisResult
        """
        self.start_execution()

        try:
            self.log_info(f"Analyzing competitors for {startup.name}")

            novelty_raw = tech_analysis.novelty_score * 7.5
            defensibility_raw = tech_analysis.defensibility_score * 7.5
            market_growth_raw = market_analysis.market_growth_potential * 5.0
            commercial_raw = market_analysis.commercial_feasibility_score * 5.0

            tech_strength = novelty_raw + defensibility_raw
            market_strength = market_growth_raw + commercial_raw
            startup_total_score = tech_strength + market_strength

            top_3_companies, sorted_scores, used_step1_scores = self._select_top_3_companies(
                startup_name=startup.name,
                startup_fallback_score=startup_total_score,
                step1_company_scores=step1_company_scores,
            )
            top_3_score_map = {
                company_name: score
                for company_name, score in sorted_scores[:3]
            }

            startup_rank = next(
                (idx + 1 for idx, (name, _) in enumerate(sorted_scores) if name == startup.name),
                None
            )
            rank_text = f"ranked #{startup_rank}" if startup_rank else "rank unavailable"

            result = CompetitorAnalysisResult(
                comparable_competitors=top_3_companies,
                comparable_competitor_scores=top_3_score_map,
                technology_differentiation=(
                    f"Derived from Step 1 tech signals "
                    f"(novelty={tech_analysis.novelty_score:.2f}, "
                    f"defensibility={tech_analysis.defensibility_score:.2f})"
                ),
                technology_differentiation_score=tech_strength,
                market_position_analysis=(
                    f"Step 1 composite score {startup_total_score:.2f}/25; {rank_text} "
                    f"among {len(sorted_scores)} companies"
                ),
                relative_barriers_to_entry=defensibility_raw,     # 0~7.5
                competitive_advantage_score=startup_total_score,  # 0~25
            )

            # Identify relative strengths
            if tech_analysis.novelty_score > 0.65:
                result.relative_strengths.append("Superior technology differentiation")
            if market_analysis.market_growth_potential > 0.70:
                result.relative_strengths.append("Larger addressable market opportunity")
            if tech_analysis.defensibility_score > 0.65:
                result.relative_strengths.append("Stronger barriers-to-entry from defensibility score")

            # Identify relative weaknesses
            result.relative_weaknesses = [
                "Step 2 uses Step 1 score ranking only (no external competitor retrieval)",
                "Ranking quality depends on completeness of Step 1 company scores",
            ]

            if retriever is not None:
                result.missing_information.append(
                    "Retriever input was ignored by design for Step 2 ranking mode"
                )
            if not used_step1_scores:
                result.missing_information.append(
                    "No Step 1 company score list provided; ranking used current startup fallback score only"
                )

            result.summary = f"Competitive Advantage Score: {result.competitive_advantage_score:.2f}. " \
                           f"Top companies from Step 1 total scores: {', '.join(result.comparable_competitors)}."

            self.log_info(f"Competitive analysis complete for {startup.name}")

            return result

        finally:
            self.end_execution()
