# AgTech Startup Investment Evaluation Multi-Agent System

## 1. Project Overview
This project aims to build a multi-agent AI system for evaluating AgTech startups for investment screening.

The system follows a staged workflow:

1. Startup Discovery Agent
2. Parallel Analysis Agents
   - Technology Summary Agent
   - Marketability Evaluation Agent
   - Impact Evaluation Agent
   - Data Moat Analysis Agent
3. Competitor Comparison Agent
4. Investment Decision Agent
5. Report Generation Agent

The goal is not only to retrieve information, but to produce a structured and explainable investment evaluation report based on evidence.

---

## 2. Multi-Agent Workflow

### Step 1. Startup Discovery Agent
This agent identifies candidate AgTech startups and gathers core company-level information.

Responsibilities:
- identify startup candidates
- retrieve basic company metadata
- collect relevant internal/external documents for downstream analysis
- normalize company profiles

### Step 2. Parallel Analysis Agents
After startup discovery, four analysis agents run independently.

#### 2-1. Technology Summary Agent
Responsibilities:
- summarize core technology
- extract patents, papers, technical keywords, and novelty claims
- identify defensibility and originality signals

#### 2-2. Marketability Evaluation Agent
Responsibilities:
- evaluate target market, customer pain points, and scalability
- identify business model and adoption barriers
- analyze commercial feasibility

#### 2-3. Impact Evaluation Agent
Responsibilities:
- evaluate environmental, agricultural, and sustainability impact
- extract evidence related to efficiency, yield improvement, carbon reduction, water saving, etc.

#### 2-4. Data Moat Analysis Agent
Responsibilities:
- evaluate whether the startup has proprietary datasets, data flywheel effects, unique sensing pipelines, or difficult-to-replicate data assets
- analyze data defensibility

### Step 3. Competitor Comparison Agent
This agent compares the analyzed startup with relevant competitors.

Responsibilities:
- identify comparable startups
- compare technology differentiation
- compare market position and barriers
- detect relative strengths and weaknesses

### Step 4. Investment Decision Agent
This agent integrates outputs from all previous agents and produces an investment decision.

Responsibilities:
- aggregate evidence and category scores
- assess uncertainty and missing information
- determine whether the startup is investable or should be held for further review

### Step 5. Report Generation Agent
This agent generates the final report.

Responsibilities:
- create structured evaluation report
- summarize agent outputs
- include evidence, uncertainty, and decision rationale

---

## 3. System Design Principles
- Multi-agent pipeline, not single-step summarization
- Retrieval first, generation second
- Evidence extraction must be separated from scoring
- Missing information must be explicitly reported
- All decisions must be explainable
- Each agent should be independently testable

---

## 4. Suggested Project Structure
```text
project/
├── app/
│   ├── main.py
│   ├── config.py
│   └── orchestrator.py
│
├── agents/
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
│   ├── startup_profile.py
│   ├── retrieved_document.py
│   ├── evidence_item.py
│   ├── analysis_results.py
│   ├── competitor_result.py
│   ├── decision_result.py
│   └── full_evaluation_result.py
│
├── rag/
│   ├── retriever.py
│   ├── vectorstore.py
│   ├── chunking.py
│   └── loaders.py
│
├── evaluation/
│   ├── criteria.py
│   ├── scoring_rules.py
│   └── thresholds.py
│
├── tests/
│   ├── test_startup_discovery_agent.py
│   ├── test_technology_summary_agent.py
│   ├── test_marketability_evaluation_agent.py
│   ├── test_impact_evaluation_agent.py
│   ├── test_data_moat_analysis_agent.py
│   ├── test_competitor_comparison_agent.py
│   ├── test_investment_decision_agent.py
│   └── test_report_generation_agent.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── examples/
│
├── requirements.txt
├── .env.example
└── README.md