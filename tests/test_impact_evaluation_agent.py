"""Test impact evaluation agent."""

import pytest
from agents import ImpactEvaluationAgent
from models import StartupProfile, ImpactAnalysisResult


def test_impact_agent_initialization():
    """Test agent initialization."""
    agent = ImpactEvaluationAgent()
    assert agent.name == "ImpactEvaluationAgent"


def test_impact_evaluation_execution():
    """Test impact analysis execution."""
    agent = ImpactEvaluationAgent()
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    result = agent.execute(startup)

    assert isinstance(result, ImpactAnalysisResult)
    assert result.environmental_impact > 0.0
    assert result.agricultural_impact > 0.0
    assert len(result.sustainability_focus) > 0


def test_impact_scores():
    """Test that impact scores are valid."""
    agent = ImpactEvaluationAgent()
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    result = agent.execute(startup)

    assert 0.0 <= result.environmental_impact <= 1.0
    assert 0.0 <= result.agricultural_impact <= 1.0
