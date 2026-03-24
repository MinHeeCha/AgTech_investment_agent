"""Test investment decision agent."""

import pytest
from agents import (
    InvestmentDecisionAgent, TechnologySummaryAgent,
    MarketabilityEvaluationAgent, ImpactEvaluationAgent,
    DataMoatAnalysisAgent, CompetitorComparisonAgent
)
from models import StartupProfile, InvestmentDecision, InvestmentRecommendation


def test_investment_decision_agent_initialization():
    """Test agent initialization."""
    agent = InvestmentDecisionAgent()
    assert agent.name == "InvestmentDecisionAgent"


def test_investment_decision_execution():
    """Test investment decision execution."""
    startup = StartupProfile(
        name="TestStartup",
        founded_year=2020,
        headquarters="San Francisco",
    )

    # Get analyses from other agents
    tech_agent = TechnologySummaryAgent()
    market_agent = MarketabilityEvaluationAgent()
    impact_agent = ImpactEvaluationAgent()
    data_moat_agent = DataMoatAnalysisAgent()
    competitor_agent = CompetitorComparisonAgent()

    tech_analysis = tech_agent.execute(startup)
    market_analysis = market_agent.execute(startup)
    impact_analysis = impact_agent.execute(startup)
    data_moat_analysis = data_moat_agent.execute(startup)
    competitor_analysis = competitor_agent.execute(startup, tech_analysis, market_analysis)

    # Make decision
    decision_agent = InvestmentDecisionAgent()
    result = decision_agent.execute(
        startup, tech_analysis, market_analysis,
        impact_analysis, data_moat_analysis, competitor_analysis
    )

    assert isinstance(result, InvestmentDecision)
    assert result.recommendation in [
        InvestmentRecommendation.INVEST,
        InvestmentRecommendation.HOLD_FOR_REVIEW,
        InvestmentRecommendation.PASS,
    ]
    assert 0.0 <= result.overall_assessment_score <= 1.0
    assert 0.0 <= result.confidence_score <= 1.0


def test_investment_decision_recommendation():
    """Test that recommendation is reasonable based on scores."""
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

    tech_analysis = tech_agent.execute(startup)
    market_analysis = market_agent.execute(startup)
    impact_analysis = impact_agent.execute(startup)
    data_moat_analysis = data_moat_agent.execute(startup)
    competitor_analysis = competitor_agent.execute(startup, tech_analysis, market_analysis)

    decision_agent = InvestmentDecisionAgent()
    result = decision_agent.execute(
        startup, tech_analysis, market_analysis,
        impact_analysis, data_moat_analysis, competitor_analysis
    )

    # Verify recommendation has supporting reasons
    assert len(result.key_strengths) > 0
    assert len(result.evidence) >= 0
