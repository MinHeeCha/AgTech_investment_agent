"""Test marketability evaluation agent."""

import pytest
from agents import MarketabilityEvaluationAgent
from models import StartupProfile, MarketabilityAnalysisResult


def test_marketability_agent_initialization():
    """Test agent initialization."""
    agent = MarketabilityEvaluationAgent()
    assert agent.name == "MarketabilityEvaluationAgent"


def test_marketability_evaluation_execution():
    """Test marketability analysis execution."""
    agent = MarketabilityEvaluationAgent()
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    result = agent.execute(startup)

    assert isinstance(result, MarketabilityAnalysisResult)
    assert result.market_growth_potential > 0.0
    assert result.commercial_feasibility_score > 0.0
    assert result.business_model is not None
    assert len(result.customer_pain_points) > 0


def test_marketability_scores():
    """Test that scores are within valid range."""
    agent = MarketabilityEvaluationAgent()
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    result = agent.execute(startup)

    assert 0.0 <= result.market_growth_potential <= 1.0
    assert 0.0 <= result.commercial_feasibility_score <= 1.0
