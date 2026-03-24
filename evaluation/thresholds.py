"""Thresholds for investment decisions."""


class InvestmentThresholds:
    """Define decision thresholds for investment recommendations."""

    # Overall assessment score thresholds
    STRONG_INVEST_THRESHOLD = 0.75  # >= 75%: Strong invest signal
    INVEST_THRESHOLD = 0.60  # >= 60%: Reasonable invest signal
    HOLD_THRESHOLD = 0.40  # >= 40%: Hold for more information
    PASS_THRESHOLD = 0.0  # < 40%: Pass (not recommended)

    # Confidence thresholds
    HIGH_CONFIDENCE = 0.75
    MODERATE_CONFIDENCE = 0.50
    LOW_CONFIDENCE = 0.25

    # Category-specific thresholds
    MINIMUM_TECHNOLOGY_SCORE = 0.40  # Must have minimum tech viability
    MINIMUM_MARKET_SCORE = 0.35  # Must have some market potential
    MINIMUM_IMPACT_SCORE = 0.30  # AgTech focus requirement
    MINIMUM_DATA_MOAT_SCORE = 0.20  # Nice to have but not critical

    # Disqualifying conditions
    DISQUALIFYING_CONDITIONS = {
        "critical_information_missing": 3,  # More than 3 critical gaps → Pass
        "major_competitive_disadvantage": True,  # Clear competitive failure
        "fundamental_tech_flaws": True,  # Unresolvable technical issues
        "regulatory_blockers": True,  # Insurmountable regulatory issues
    }

    @classmethod
    def get_recommendation(cls, overall_score: float, 
                          confidence: float,
                          critical_gaps: int = 0) -> str:
        """
        Get investment recommendation based on scores.

        Args:
            overall_score: Overall assessment score (0-1)
            confidence: Confidence in the assessment (0-1)
            critical_gaps: Number of critical information gaps

        Returns:
            Recommendation: "invest", "hold_for_review", or "pass"
        """
        # Check for disqualifying number of gaps
        if critical_gaps >= cls.DISQUALIFYING_CONDITIONS["critical_information_missing"]:
            return "pass"

        # Check strong invest signal
        if overall_score >= cls.STRONG_INVEST_THRESHOLD:
            return "invest"

        # Check invest threshold
        if overall_score >= cls.INVEST_THRESHOLD:
            if confidence >= cls.MODERATE_CONFIDENCE:
                return "invest"
            else:
                return "hold_for_review"

        # Check hold threshold
        if overall_score >= cls.HOLD_THRESHOLD:
            return "hold_for_review"

        # Default to pass
        return "pass"

    @classmethod
    def get_confidence_level(cls, confidence: float) -> str:
        """
        Get confidence level description.

        Args:
            confidence: Confidence score (0-1)

        Returns:
            Confidence level: "high", "moderate", or "low"
        """
        if confidence >= cls.HIGH_CONFIDENCE:
            return "high"
        elif confidence >= cls.MODERATE_CONFIDENCE:
            return "moderate"
        else:
            return "low"

    @classmethod
    def check_minimum_requirements(cls, scores: dict[str, float]) -> tuple[bool, list[str]]:
        """
        Check if startup meets minimum requirements across categories.

        Args:
            scores: Dict of category to score

        Returns:
            Tuple of (meets_requirements, missing_reasons)
        """
        missing_reasons = []

        if scores.get("technology_novelty", 0) < cls.MINIMUM_TECHNOLOGY_SCORE:
            missing_reasons.append(
                f"Technology novelty ({scores.get('technology_novelty', 0):.2f}) below threshold ({cls.MINIMUM_TECHNOLOGY_SCORE})"
            )

        if scores.get("market_growth", 0) < cls.MINIMUM_MARKET_SCORE:
            missing_reasons.append(
                f"Market growth potential ({scores.get('market_growth', 0):.2f}) below threshold ({cls.MINIMUM_MARKET_SCORE})"
            )

        if scores.get("impact", 0) < cls.MINIMUM_IMPACT_SCORE:
            missing_reasons.append(
                f"AgTech impact ({scores.get('impact', 0):.2f}) below threshold ({cls.MINIMUM_IMPACT_SCORE})"
            )

        meets_requirements = len(missing_reasons) == 0
        return meets_requirements, missing_reasons
