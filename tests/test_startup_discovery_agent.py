"""Test base agent."""

import pytest
from agents import StartupDiscoveryAgent
from models import StartupProfile


def test_startup_discovery_agent_initialization():
    """Test agent initialization."""
    agent = StartupDiscoveryAgent()
    assert agent.name == "StartupDiscoveryAgent"
    assert agent.description is not None


def test_startup_discovery_execution():
    """Test startup discovery execution."""
    agent = StartupDiscoveryAgent()
    startup_name = "TestStartup"
    additional_info = {
        "founded_year": 2020,
        "headquarters": "San Francisco",
        "stage": "Series A",
    }

    result = agent.execute(startup_name, additional_info=additional_info)

    assert isinstance(result, StartupProfile)
    assert result.name == startup_name
    assert result.founded_year == 2020
    assert result.headquarters == "San Francisco"
    assert result.stage == "Series A"


def test_startup_discovery_batch():
    """Test batch startup discovery."""
    agent = StartupDiscoveryAgent()
    startup_names = ["Startup1", "Startup2", "Startup3"]

    results = agent.batch_discover(startup_names)

    assert len(results) == 3
    for i, result in enumerate(results):
        assert isinstance(result, StartupProfile)
        assert result.name == startup_names[i]
