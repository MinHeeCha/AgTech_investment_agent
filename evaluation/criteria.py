"""Evaluation criteria for investment assessment."""


class EvaluationCriteria:
    """Define evaluation criteria and their weights."""

    # Technology criteria (25% weight)
    TECHNOLOGY_CRITERIA = {
        "novelty": {
            "weight": 0.40,
            "description": "Technical innovation and originality",
        },
        "defensibility": {
            "weight": 0.35,
            "description": "IP protection and moat strength",
        },
        "feasibility": {
            "weight": 0.25,
            "description": "Technical feasibility and maturity",
        },
    }

    # Market criteria (25% weight)
    MARKET_CRITERIA = {
        "market_size": {
            "weight": 0.30,
            "description": "Total addressable market",
        },
        "growth_potential": {
            "weight": 0.35,
            "description": "Market growth rate and opportunity",
        },
        "commercial_viability": {
            "weight": 0.35,
            "description": "Business model and adoption likelihood",
        },
    }

    # Impact criteria (20% weight)
    IMPACT_CRITERIA = {
        "environmental": {
            "weight": 0.40,
            "description": "Environmental impact and sustainability",
        },
        "agricultural": {
            "weight": 0.40,
            "description": "Direct agricultural benefits",
        },
        "measurability": {
            "weight": 0.20,
            "description": "Clarity and measurability of impact claims",
        },
    }

    # Data Moat criteria (15% weight)
    DATA_MOAT_CRITERIA = {
        "data_assets": {
            "weight": 0.40,
            "description": "Proprietary data assets and uniqueness",
        },
        "network_effects": {
            "weight": 0.35,
            "description": "Data flywheel and network effects",
        },
        "defensibility": {
            "weight": 0.25,
            "description": "Difficulty to replicate or compete",
        },
    }

    # Competitive criteria (15% weight)
    COMPETITIVE_CRITERIA = {
        "differentiation": {
            "weight": 0.40,
            "description": "Clear differentiation from competitors",
        },
        "barriers": {
            "weight": 0.35,
            "description": "Barriers to entry and substitution",
        },
        "market_position": {
            "weight": 0.25,
            "description": "Current and potential market position",
        },
    }

    # Overall weights
    OVERALL_WEIGHTS = {
        "technology": 0.25,
        "market": 0.25,
        "impact": 0.20,
        "data_moat": 0.15,
        "competitive": 0.15,
    }

    @classmethod
    def get_criterion_weight(cls, category: str, criterion: str) -> float:
        """Get the weight of a specific criterion."""
        criteria_map = {
            "technology": cls.TECHNOLOGY_CRITERIA,
            "market": cls.MARKET_CRITERIA,
            "impact": cls.IMPACT_CRITERIA,
            "data_moat": cls.DATA_MOAT_CRITERIA,
            "competitive": cls.COMPETITIVE_CRITERIA,
        }

        if category not in criteria_map:
            return 0.0

        criterion_data = criteria_map[category].get(criterion, {})
        return criterion_data.get("weight", 0.0)

    @classmethod
    def get_category_weight(cls, category: str) -> float:
        """Get the overall weight of a category."""
        return cls.OVERALL_WEIGHTS.get(category, 0.0)
