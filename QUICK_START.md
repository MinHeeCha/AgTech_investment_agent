# Quick Reference Guide

## Project Overview

Multi-agent system for evaluating AgTech startups with 8 specialized agents across 5 sequential stages.

## Quick Start

```bash
# 1. Navigate to project
cd AgTech_investment_agent

# 2. Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env if needed

# 4. Run evaluation
python run_evaluation.py

# 5. Check outputs
ls -la outputs/
```

## File Organization

```
agents/          → 8 agents + base class
models/          → 10 data store classes
rag/             → Document retrieval system
evaluation/      → Scoring & thresholds
app/             → Config & orchestrator
tests/           → 11 test files
```

## The 8 Agents

| # | Name | Stage | Output |
|-|-|-|-|
| 1 | StartupDiscoveryAgent | 0 | StartupProfile |
| 2 | TechnologySummaryAgent | 1 | TechnologyAnalysisResult |
| 3 | MarketabilityEvaluationAgent | 1 | MarketabilityAnalysisResult |
| 4 | ImpactEvaluationAgent | 1 | ImpactAnalysisResult |
| 5 | DataMoatAnalysisAgent | 1 | DataMoatAnalysisResult |
| 6 | CompetitorComparisonAgent | 2 | CompetitorAnalysisResult |
| 7 | InvestmentDecisionAgent | 3 | InvestmentDecision |
| 8 | ReportGenerationAgent | 4 | FullEvaluationResult |

## Five Scoring Categories

- **Technology** (25%): Novelty, Defensibility, Feasibility
- **Market** (25%): Size, Growth, Viability
- **Impact** (20%): Environmental, Agricultural, Measurability
- **Data Moat** (15%): Assets, Flywheel, Defensibility
- **Competitive** (15%): Differentiation, Barriers, Position

## Investment Decisions

- ✅ **≥0.75**: INVEST (Strong)
- ✅ **0.60-0.74**: INVEST (Conditional)
- 🟡 **0.40-0.59**: HOLD_FOR_REVIEW
- ❌ **<0.40**: PASS

## Usage Examples

### Single Startup

```python
from app import AgentOrchestrator

orchestrator = AgentOrchestrator()
result = orchestrator.evaluate_startup("StartupName", {
    "founded_year": 2020,
    "headquarters": "San Francisco",
    "stage": "Series A"
})

print(result.investment_decision.recommendation)
print(result.report_content)
```

### Multiple Startups

```python
results = orchestrator.evaluate_multiple_startups([
    "Startup1", "Startup2", "Startup3"
])

for r in results:
    print(f"{r.startup.name}: {r.investment_decision.recommendation}")
```

### With Documents

```python
from rag import Retriever, DocumentLoader

retriever = Retriever()
docs = DocumentLoader.load_directory("./docs")
retriever.add_documents(docs)

orchestrator = AgentOrchestrator(retriever)
result = orchestrator.evaluate_startup("StartupName")
```

## Testing

```bash
# All tests
pytest tests/ -v

# Coverage report
pytest tests/ --cov=. --cov-report=html

# Specific test
pytest tests/test_orchestrator.py -v

# Watch mode
pytest-watch tests/
```

## Output Files

Each evaluation generates:
- `{name}_evaluation_report.txt` - Detailed text report
- `{name}_evaluation_summary.json` - Structured data

## Configuration

Edit `.env`:
```
LLM_MODEL=claude-3-haiku
EMBEDDING_MODEL=BAAI/bge-m3
MAX_PARALLEL_WORKERS=4
INVEST_THRESHOLD=0.60
```

## Key Classes

### AgentOrchestrator
```python
orchestrator = AgentOrchestrator(retriever, max_workers=4)
result = orchestrator.evaluate_startup(name, info)
results = orchestrator.evaluate_multiple_startups(names)
```

### FullEvaluationResult
```python
result.startup                    # StartupProfile
result.technology_analysis       # TechnologyAnalysisResult
result.marketability_analysis    # MarketabilityAnalysisResult
result.impact_analysis           # ImpactAnalysisResult
result.data_moat_analysis        # DataMoatAnalysisResult
result.competitor_analysis       # CompetitorAnalysisResult
result.investment_decision       # InvestmentDecision
result.report_content            # Full text report
```

### Retriever
```python
from rag import Retriever, DocumentLoader

retriever = Retriever()
docs = DocumentLoader.load_text_file("file.txt")
retriever.add_documents([docs])
results = retriever.retrieve("query", top_k=5)
```

## Common Tasks

### Add a New Evaluation Criterion

1. Edit `evaluation/criteria.py` - Add to appropriate category
2. Update scoring in agent files
3. Adjust thresholds in `evaluation/thresholds.py`
4. Add test in `tests/`

### Create a Custom Agent

1. Create `agents/stage_agentname.py`
2. Inherit from `BaseAgent`
3. Implement `execute()` method
4. Add to orchestrator workflow
5. Create test file

### Load Your Documents

```python
from rag import DocumentLoader

# Load single file
doc = DocumentLoader.load_text_file("file.txt")

# Load directory
docs = DocumentLoader.load_directory("./documents", "*.md")

# Add to retriever
retriever.add_documents(docs)
```

## Debugging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check agent execution:
```python
agent = TechSummaryAgent()
agent.start_execution()
result = agent.execute(startup)
agent.end_execution()
print(agent.get_execution_duration())
```

## File Locations

- **Agents**: `agents/`
- **Data Models**: `models/`
- **RAG System**: `rag/`
- **Evaluation Rules**: `evaluation/`
- **Tests**: `tests/`
- **Outputs**: `outputs/`
- **Data**: `data/`

## Important Concepts

### Evidence Item
Every finding backed by source document with confidence score

### Score Range
All scores normalized to 0.0-1.0 range

### Parallel Execution
Stage 2 agents run concurrently using ThreadPoolExecutor

### Weighted Aggregation
Final score combines 5 categories with predefined weights

### Decision Thresholds
Clear cutoffs for INVEST/HOLD/PASS recommendations

## Troubleshooting

**Import errors?**
- Ensure `.env` is set up
- Check Python path includes project root
- Verify all `__init__.py` files exist

**Tests failing?**
- Run `pytest -v` for details
- Check that all dependencies are installed
- Verify Python version is 3.10+

**Missing outputs?**
- Check `outputs/` directory exists
- Verify write permissions
- Check `LOG_FILE` in `.env`

## Performance

- Single startup evaluation: ~5-10 seconds
- Parallel stage 2: ~50% time reduction
- 100 startups: ~5-10 minutes
- Database storage: Recommended for scaling

## Next Steps

1. Integrate real LLM APIs
2. Add actual embedding models
3. Connect to startup databases
4. Deploy as web service
5. Add visualization dashboard
6. Train on historical data
7. Optimize scoring weights

---

**Need help?** Check `IMPLEMENTATION_SUMMARY.md` for detailed overview.
