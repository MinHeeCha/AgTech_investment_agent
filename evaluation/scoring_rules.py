"""Scoring rules for evaluation."""


class ScoringRules:
    """Define rules for scoring different evaluation dimensions."""

    # Novelty scoring
    NOVELTY_TIERS = {
        "breakthrough": {"range": (0.85, 1.0), "description": "Paradigm-shifting innovation"},
        "significant": {"range": (0.70, 0.84), "description": "Significant technical advancement"},
        "moderate": {"range": (0.50, 0.69), "description": "Moderate improvement"},
        "incremental": {"range": (0.30, 0.49), "description": "Incremental improvement"},
        "commercial": {"range": (0.0, 0.29), "description": "Commercial application of existing tech"},
    }

    # Defensibility scoring
    DEFENSIBILITY_TIERS = {
        "very_strong": {"range": (0.85, 1.0), "description": "Multiple strong IP/moat"},
        "strong": {"range": (0.70, 0.84), "description": "Strong IP position or technical moat"},
        "moderate": {"range": (0.50, 0.69), "description": "Some defensibility mechanisms"},
        "weak": {"range": (0.30, 0.49), "description": "Limited defensibility"},
        "vulnerable": {"range": (0.0, 0.29), "description": "Easily replicable"},
    }

    # Market growth potential
    MARKET_GROWTH_TIERS = {
        "exceptional": {"range": (0.85, 1.0), "description": ">30% CAGR"},
        "strong": {"range": (0.70, 0.84), "description": "20-30% CAGR"},
        "good": {"range": (0.55, 0.69), "description": "10-20% CAGR"},
        "moderate": {"range": (0.40, 0.54), "description": "5-10% CAGR"},
        "modest": {"range": (0.0, 0.39), "description": "<5% CAGR"},
    }

    # Commercial feasibility
    FEASIBILITY_TIERS = {
        "very_high": {"range": (0.85, 1.0), "description": "Clear path to revenue"},
        "high": {"range": (0.70, 0.84), "description": "Realistic commercialization plan"},
        "moderate": {"range": (0.50, 0.69), "description": "Some commercialization challenges"},
        "low": {"range": (0.30, 0.49), "description": "Significant commercialization challenges"},
        "very_low": {"range": (0.0, 0.29), "description": "Unclear commercialization path"},
    }

    @staticmethod
    def normalize_score(score: float) -> float:
        """
        Ensure score is within [0.0, 1.0] range.

        Args:
            score: Score value

        Returns:
            Normalized score
        """
        return max(0.0, min(1.0, score))

    @staticmethod
    def weighted_average(scores: dict[str, float]) -> float:
        """
        Calculate weighted average of scores.

        Args:
            scores: Dict of {score_name: score_value}

        Returns:
            Weighted average
        """
        if not scores:
            return 0.0

        total = sum(scores.values())
        count = len(scores)
        return total / count if count > 0 else 0.0

    @staticmethod
    def get_tier_for_score(score: float, tier_map: dict) -> str:
        """
        Determine which tier a score falls into.

        Args:
            score: Score value
            tier_map: Map of tier_name to range/description

        Returns:
            Tier name
        """
        for tier_name, tier_data in tier_map.items():
            score_range = tier_data.get("range", (0, 1))
            if score_range[0] <= score <= score_range[1]:
                return tier_name

        return list(tier_map.keys())[0]

    @staticmethod
    def aggregate_scores(category_scores: dict[str, float],
                        weights: dict[str, float]) -> float:
        """
        Aggregate multiple category scores with weights.

        Args:
            category_scores: Dict of category to score
            weights: Dict of category to weight

        Returns:
            Aggregate score
        """
        total_score = 0.0
        total_weight = 0.0

        for category, score in category_scores.items():
            weight = weights.get(category, 0.0)
            total_score += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return ScoringRules.normalize_score(total_score / total_weight)
