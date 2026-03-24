"""Test report generation agent."""

import pytest
from agents import (
    ReportGenerationAgent, TechnologySummaryAgent,
    MarketabilityEvaluationAgent, ImpactEvaluationAgent,
    DataMoatAnalysisAgent, CompetitorComparisonAgent,
    InvestmentDecisionAgent
)
from models import StartupProfile, FullEvaluationResult


def test_report_generation_agent_initialization():
    """Test agent initialization."""
    agent = ReportGenerationAgent()
    assert agent.name == "ReportGenerationAgent"


def test_report_generation_execution():
    """Test report generation execution."""
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    # Get all analyses
    tech_agent = TechnologySummaryAgent()
    market_agent = MarketabilityEvaluationAgent()
    impact_agent = ImpactEvaluationAgent()
    data_moat_agent = DataMoatAnalysisAgent()
    competitor_agent = CompetitorComparisonAgent()
    decision_agent = InvestmentDecisionAgent()

    tech_analysis = tech_agent.execute(startup)
    market_analysis = market_agent.execute(startup)
    impact_analysis = impact_agent.execute(startup)
    data_moat_analysis = data_moat_agent.execute(startup)
    competitor_analysis = competitor_agent.execute(startup, tech_analysis, market_analysis)
    investment_decision = decision_agent.execute(
        startup, tech_analysis, market_analysis,
        impact_analysis, data_moat_analysis, competitor_analysis
    )

    # Generate report
    report_agent = ReportGenerationAgent()
    result = report_agent.execute(
        startup, tech_analysis, market_analysis,
        impact_analysis, data_moat_analysis,
        competitor_analysis, investment_decision
    )

    assert isinstance(result, FullEvaluationResult)
    assert result.report_content is not None
    assert len(result.report_content) > 100
    assert "AGTECH STARTUP INVESTMENT EVALUATION REPORT" in result.report_content


def test_report_content_completeness():
    """Test that report contains all required sections."""
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    tech_agent = TechnologySummaryAgent()
    market_agent = MarketabilityEvaluationAgent()
    impact_agent = ImpactEvaluationAgent()
    data_moat_agent = DataMoatAnalysisAgent()
    competitor_agent = CompetitorComparisonAgent()
    decision_agent = InvestmentDecisionAgent()

    tech_analysis = tech_agent.execute(startup)
    market_analysis = market_agent.execute(startup)
    impact_analysis = impact_agent.execute(startup)
    data_moat_analysis = data_moat_agent.execute(startup)
    competitor_analysis = competitor_agent.execute(startup, tech_analysis, market_analysis)
    investment_decision = decision_agent.execute(
        startup, tech_analysis, market_analysis,
        impact_analysis, data_moat_analysis, competitor_analysis
    )

    report_agent = ReportGenerationAgent()
    result = report_agent.execute(
        startup, tech_analysis, market_analysis,
        impact_analysis, data_moat_analysis,
        competitor_analysis, investment_decision
    )

    # Check for key sections
    required_sections = [
        "EXECUTIVE SUMMARY",
        "TECHNOLOGY ANALYSIS",
        "MARKET ANALYSIS",
        "IMPACT ANALYSIS",
        "DATA MOAT ANALYSIS",
        "COMPETITIVE ANALYSIS",
        "INVESTMENT DECISION",
    ]

    for section in required_sections:
        assert section in result.report_content
