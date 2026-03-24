"""Test orchestrator."""

import pytest
from app.orchestrator import AgentOrchestrator
from models import FullEvaluationResult


def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    orchestrator = AgentOrchestrator()
    assert orchestrator is not None
    assert orchestrator.discovery_agent is not None
    assert orchestrator.tech_agent is not None


def test_orchestrator_workflow_summary():
    """Test workflow summary."""
    orchestrator = AgentOrchestrator()
    summary = orchestrator.get_workflow_summary()

    assert summary["stages"] == 5
    assert summary["total_agents"] == 8
    assert summary["parallel_agents"] == 4
    assert len(summary["workflow"]) == 5


def test_orchestrator_single_startup_evaluation():
    """Test evaluation of a single startup."""
    orchestrator = AgentOrchestrator()

    startup_info = {
        "founded_year": 2020,
        "headquarters": "San Francisco",
        "stage": "Series A",
    }

    result = orchestrator.evaluate_startup("TestStartup", startup_info)

    assert isinstance(result, FullEvaluationResult)
    assert result.startup.name == "TestStartup"
    assert result.technology_analysis is not None
    assert result.marketability_analysis is not None
    assert result.impact_analysis is not None
    assert result.data_moat_analysis is not None
    assert result.competitor_analysis is not None
    assert result.investment_decision is not None
    assert result.report_content is not None


def test_orchestrator_multiple_startup_evaluation():
    """Test evaluation of multiple startups."""
    orchestrator = AgentOrchestrator()

    startup_names = ["Startup1", "Startup2", "Startup3"]
    results = orchestrator.evaluate_multiple_startups(startup_names)

    assert len(results) == 3
    for i, result in enumerate(results):
        assert isinstance(result, FullEvaluationResult)
        assert result.startup.name == startup_names[i]
