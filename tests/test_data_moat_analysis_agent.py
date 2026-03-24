"""Test data moat analysis agent."""

import pytest
from agents import DataMoatAnalysisAgent
from models import StartupProfile, DataMoatAnalysisResult


def test_data_moat_agent_initialization():
    """Test agent initialization."""
    agent = DataMoatAnalysisAgent()
    assert agent.name == "DataMoatAnalysisAgent"


def test_data_moat_execution():
    """Test data moat analysis execution."""
    agent = DataMoatAnalysisAgent()
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    result = agent.execute(startup)

    assert isinstance(result, DataMoatAnalysisResult)
    assert result.moat_strength_score > 0.0
    assert result.dataset_defensibility_score >= 0.0
    assert result.data_flywheel_potential >= 0.0


def test_data_moat_scores():
    """Test that data moat scores are within valid range."""
    agent = DataMoatAnalysisAgent()
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    result = agent.execute(startup)

    assert 0.0 <= result.moat_strength_score <= 1.0
    assert 0.0 <= result.dataset_defensibility_score <= 1.0
    assert 0.0 <= result.data_flywheel_potential <= 1.0
