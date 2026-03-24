# AgTech Startup Investment Evaluation Multi-Agent System

## Overview

A comprehensive multi-agent AI system for evaluating AgTech startups for investment potential. The system orchestrates specialized agents to analyze technology, market, impact, competitive position, and other critical factors for investment decision-making.

## System Architecture

### Multi-Agent Workflow

The system follows a 5-stage pipeline with 8 specialized agents:

```
Stage 1: Startup Discovery
    ↓
Stage 2: Parallel Analysis (4 agents)
    ├─ Technology Summary Agent
    ├─ Marketability Evaluation Agent
    ├─ Impact Evaluation Agent
    └─ Data Moat Analysis Agent
    ↓
Stage 3: Competitor Comparison
    ↓
Stage 4: Investment Decision
    ↓
Stage 5: Report Generation
```

### Agent Responsibilities

#### 1. **StartupDiscoveryAgent** (Stage 1)
- Identifies and profiles startup candidates
- Retrieves basic company metadata
- Gathers relevant documents for downstream analysis
- Normalizes company profiles

#### 2. **TechnologySummaryAgent** (Stage 2, Parallel)
- Summarizes core technology
- Extracts patents, papers, technical keywords
- Identifies defensibility and originality signals
- **Score Range**: Novelty (0-1), Defensibility (0-1)

#### 3. **MarketabilityEvaluationAgent** (Stage 2, Parallel)
- Evaluates target market and customer pain points
- Analyzes business model and adoption barriers
- Assesses commercial feasibility
- **Score Range**: Market Growth (0-1), Feasibility (0-1)

#### 4. **ImpactEvaluationAgent** (Stage 2, Parallel)
- Evaluates environmental and agricultural impact
- Extracts efficiency and yield improvement claims
- Analyzes sustainability benefits
- **Score Range**: Environmental (0-1), Agricultural (0-1)

#### 5. **DataMoatAnalysisAgent** (Stage 2, Parallel)
- Analyzes proprietary datasets
- Evaluates data flywheel effects
- Assesses data defensibility
- **Score Range**: Moat Strength (0-1)

#### 6. **CompetitorComparisonAgent** (Stage 3)
- Identifies comparable competitors
- Compares technology differentiation
- Analyzes relative market position
- **Score Range**: Competitive Advantage (0-1)

#### 7. **InvestmentDecisionAgent** (Stage 4)
- Aggregates evidence from all agents
- Calculates overall assessment score
- Produces investment recommendation
- **Recommendations**: INVEST, HOLD_FOR_REVIEW, PASS

#### 8. **ReportGenerationAgent** (Stage 5)
- Creates comprehensive evaluation report
- Summarizes all agent findings
- Documents evidence and decision rationale

## Evaluation Framework

### Scoring Criteria

**Technology (25% weight)**
- Novelty: Technical innovation and originality
- Defensibility: IP protection and moat strength
- Feasibility: Technical feasibility and maturity

**Market (25% weight)**
- Market Size: Total addressable market
- Growth Potential: Market growth rate and opportunity
- Commercial Viability: Business model and adoption likelihood

**Impact (20% weight)**
- Environmental: Environmental sustainability impact
- Agricultural: Direct agricultural benefits
- Measurability: Clarity of impact claims

**Data Moat (15% weight)**
- Data Assets: Proprietary data assets
- Network Effects: Data flywheel potential
- Defensibility: Difficulty to replicate

**Competitive Position (15% weight)**
- Differentiation: Clear market differentiation
- Barriers: Barriers to entry and substitution
- Market Position: Current and potential positioning

### Investment Thresholds

- **Strong Invest (≥0.75)**: Clear investment opportunity with strong signals across most criteria
- **Invest (0.60-0.74)**: Reasonable investment opportunity with good evidence
- **Hold for Review (0.40-0.59)**: Promising but needs further evaluation
- **Pass (<0.40)**: Not recommended for investment at this time

## Project Structure

```
AgTech_investment_agent/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── orchestrator.py        # Multi-agent workflow orchestrator
│   └── main.py                # Main application entry point
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Abstract base agent class
│   ├── 0_startup_discovery_agent.py
│   ├── 1_technology_summary_agent.py
│   ├── 1_marketability_evaluation_agent.py
│   ├── 1_impact_evaluation_agent.py
│   ├── 1_data_moat_analysis_agent.py
│   ├── 2_competitor_comparison_agent.py
│   ├── 3_investment_decision_agent.py
│   └── 4_report_generation_agent.py
│
├── models/
│   ├── __init__.py
│   ├── startup_profile.py     # Startup data model
│   ├── retrieved_document.py  # Retrieved document model
│   ├── evidence_item.py       # Evidence item model
│   ├── analysis_results.py    # Analysis result models
│   ├── competitor_result.py   # Competitor analysis model
│   ├── decision_result.py     # Investment decision model
│   └── full_evaluation_result.py  # Complete evaluation report
│
├── rag/
│   ├── __init__.py
│   ├── chunking.py            # Document chunking strategies
│   ├── vectorstore.py         # Vector storage and search
│   ├── retriever.py           # RAG-based retrieval
│   └── loaders.py             # Document loading utilities
│
├── evaluation/
│   ├── __init__.py
│   ├── criteria.py            # Evaluation criteria and weights
│   ├── scoring_rules.py       # Scoring rules and aggregation
│   └── thresholds.py          # Decision thresholds
│
├── tests/
│   ├── __init__.py
│   ├── test_startup_discovery_agent.py
│   ├── test_technology_summary_agent.py
│   ├── test_marketability_evaluation_agent.py
│   ├── test_impact_evaluation_agent.py
│   ├── test_data_moat_analysis_agent.py
│   ├── test_competitor_comparison_agent.py
│   ├── test_investment_decision_agent.py
│   ├── test_report_generation_agent.py
│   └── test_orchestrator.py
│
├── data/
│   ├── raw/                   # Raw input data
│   ├── processed/             # Processed data
│   └── examples/              # Example data files
│
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── setup.py                  # Package setup configuration
├── pytest.ini                # Pytest configuration
├── run_evaluation.py         # Quick start script
├── .github/workflows/        # CI/CD configuration
└── README.md                 # This file
```

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AgTech_investment_agent
```

### 2. Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Quick Start

```bash
python run_evaluation.py
```

### Programmatic Usage

```python
from app import AgentOrchestrator

# Create orchestrator
orchestrator = AgentOrchestrator()

# Evaluate a single startup
startup_info = {
    "founded_year": 2020,
    "headquarters": "San Francisco, CA",
    "stage": "Series A",
}

result = orchestrator.evaluate_startup("MyStartup", startup_info)

# Access results
print(f"Recommendation: {result.investment_decision.recommendation}")
print(f"Score: {result.investment_decision.overall_assessment_score:.2%}")
print(f"Report:\n{result.report_content}")
```

### Batch Evaluation

```python
from app import AgentOrchestrator

orchestrator = AgentOrchestrator()

startup_names = ["Startup1", "Startup2", "Startup3"]
results = orchestrator.evaluate_multiple_startups(startup_names)

for result in results:
    print(f"{result.startup.name}: {result.investment_decision.recommendation}")
```

### With Custom Documents (RAG)

```python
from app import AgentOrchestrator
from rag import Retriever, DocumentLoader

# Load documents
retriever = Retriever()
loader = DocumentLoader()
docs = loader.load_directory("./startup_documents", "*.txt")
retriever.add_documents(docs)

# Create orchestrator with retriever
orchestrator = AgentOrchestrator(retriever)

# Evaluate with document context
result = orchestrator.evaluate_startup("MyStartup")
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_orchestrator.py -v

# Run with markers
pytest -m "unit"
```

## Configuration

Edit `.env` file to configure:

```bash
# LLM Configuration
LLM_MODEL=claude-3-haiku
EMBEDDING_MODEL=BAAI/bge-m3
OPENAI_API_KEY=your_key_here

# RAG Configuration
CHUNK_SIZE=1024
TOP_K_RETRIEVAL=5

# Agent Configuration
MAX_PARALLEL_WORKERS=4

# Evaluation Thresholds
STRONG_INVEST_THRESHOLD=0.75
INVEST_THRESHOLD=0.60
```

## Output Files

The system generates two files per evaluated startup:

1. **Full Report** (`{startup_name}_evaluation_report.txt`)
   - Comprehensive human-readable report
   - Detailed analysis from each agent
   - Investment recommendation and rationale

2. **JSON Summary** (`{startup_name}_evaluation_summary.json`)
   - Structured data format
   - Scores and metrics
   - Suitable for further processing

## Design Principles

- **Multi-agent pipeline**: Specialized agents with clear responsibilities
- **Retrieval first**: Evidence extraction before scoring
- **Transparency**: All decisions are explainable with supporting evidence
- **Modularity**: Each agent is independently testable
- **Parallel execution**: 4 analysis agents run concurrently for efficiency
- **Evidence-based**: All recommendations backed by specific evidence

## Key Features

✅ **Multi-agent architecture** with specialized expertise  
✅ **Parallel execution** for efficient evaluation  
✅ **RAG integration** for document-based analysis  
✅ **Structured evaluation** with explicit criteria and weights  
✅ **Evidence tracking** for decision transparency  
✅ **Comprehensive reporting** with actionable insights  
✅ **Extensible design** for custom agents and criteria  
✅ **Comprehensive testing** with pytest coverage  

## Future Enhancements

- [ ] Integration with real LLM APIs (OpenAI, Anthropic)
- [ ] Database persistence for evaluation results
- [ ] Web dashboard for report visualization
- [ ] Real document ingestion (PDFs, websites)
- [ ] Actual embedding model integration
- [ ] Vector database support (Chroma, Pinecone)
- [ ] API endpoint for remote evaluation
- [ ] Machine learning for criteria weighting optimization
- [ ] Historical performance tracking
- [ ] Comparative analysis across multiple startups

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues, questions, or suggestions, please open an issue on the repository.

---

**Last Updated**: March 2026  
**Version**: 1.0.0
