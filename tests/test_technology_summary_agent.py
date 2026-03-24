"""Test technology summary agent."""

import pytest
from agents import TechnologySummaryAgent
from models import StartupProfile, TechnologyAnalysisResult


def test_technology_summary_agent_initialization():
    """Test agent initialization."""
    agent = TechnologySummaryAgent()
    assert agent.name == "TechnologySummaryAgent"


def test_technology_summary_execution():
    """Test technology analysis execution."""
    agent = TechnologySummaryAgent()
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    result = agent.execute(startup)

    assert isinstance(result, TechnologyAnalysisResult)
    assert result.novelty_score > 0.0
    assert result.defensibility_score > 0.0
    assert result.core_technology is not None
    assert len(result.technical_keywords) > 0


def test_technology_summary_scores():
    """Test that scores are reasonable."""
    agent = TechnologySummaryAgent()
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    result = agent.execute(startup)

    assert 0.0 <= result.novelty_score <= 1.0
    assert 0.0 <= result.defensibility_score <= 1.0
