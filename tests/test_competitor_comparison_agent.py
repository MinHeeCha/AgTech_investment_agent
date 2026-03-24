"""Test competitor comparison agent."""

import pytest
from agents import CompetitorComparisonAgent, TechnologySummaryAgent, MarketabilityEvaluationAgent
from models import StartupProfile, CompetitorAnalysisResult


def test_competitor_agent_initialization():
    """Test agent initialization."""
    agent = CompetitorComparisonAgent()
    assert agent.name == "CompetitorComparisonAgent"


def test_competitor_comparison_execution():
    """Test competitor comparison execution."""
    agent = CompetitorComparisonAgent()
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    tech_agent = TechnologySummaryAgent()
    market_agent = MarketabilityEvaluationAgent()

    tech_analysis = tech_agent.execute(startup)
    market_analysis = market_agent.execute(startup)

    result = agent.execute(startup, tech_analysis, market_analysis)

    assert isinstance(result, CompetitorAnalysisResult)
    assert result.competitive_advantage_score >= 0.0
    assert len(result.comparable_competitors) > 0


def test_competitor_scores():
    """Test that competitor scores are valid."""
    agent = CompetitorComparisonAgent()
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    tech_agent = TechnologySummaryAgent()
    market_agent = MarketabilityEvaluationAgent()

    tech_analysis = tech_agent.execute(startup)
    market_analysis = market_agent.execute(startup)

    result = agent.execute(startup, tech_analysis, market_analysis)

    assert 0.0 <= result.competitive_advantage_score <= 1.0
    assert 0.0 <= result.technology_differentiation_score <= 1.0
