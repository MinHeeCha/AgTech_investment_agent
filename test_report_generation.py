"""Test script for ReportGenerationAgent - generates PDF report with dummy data."""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.step4_report_generation_agent import ReportGenerationAgent
from models import (
    StartupProfile,
    TechnologyAnalysisResult,
    MarketabilityAnalysisResult,
    ImpactAnalysisResult,
    DataMoatAnalysisResult,
    CompetitorAnalysisResult,
    InvestmentDecision,
    InvestmentRecommendation,
    EvidenceItem,
)


def create_dummy_startup() -> StartupProfile:
    """Create dummy startup profile."""
    return StartupProfile(
        name="TechFarm AI",
        founded_year=2020,
        headquarters="San Francisco, CA",
        stage="Series A",
        description="AI-powered precision agriculture platform using computer vision and ML models",
        industry="AgTech",
        target_markets=["North America", "Western Europe"],
        website="https://techfarmai.example.com",
    )


def create_dummy_technology_analysis() -> TechnologyAnalysisResult:
    """Create dummy technology analysis result."""
    return TechnologyAnalysisResult(
        core_technology="Deep learning-based crop disease detection system using hyperspectral imaging and real-time monitoring",
        novelty_score=0.78,
        defensibility_score=0.72,
        patents=[
            "US Patent 11,234,567: Deep Learning Disease Detection Method",
            "WO/2023/567890: Hyperspectral Image Processing System",
        ],
        research_papers=[
            "Proceedings of IEEE ICRA 2023: Real-time Crop Analysis",
            "Journal of Agricultural Computing Vol. 15: Precision Agriculture AI",
        ],
        technical_keywords=[
            "deep learning",
            "computer vision",
            "hyperspectral imaging",
            "precision agriculture",
            "IoT sensors",
        ],
        evidence=[
            EvidenceItem(
                claim="Proprietary deep learning model for disease detection",
                source_document="Technical Whitepaper v2.1",
                evidence_type="Technical Document",
                confidence=0.85,
                supporting_details="Achieves 96% accuracy on crop disease detection across 50+ crop types"
            ),
            EvidenceItem(
                claim="Filed 2 patent applications with USPTO",
                source_document="Patent Filing History",
                evidence_type="Patent",
                confidence=0.95,
                supporting_details="Core algorithms and sensor integration protected"
            ),
        ],
        missing_information=[],
        summary="TechFarm AI has developed a differentiated deep learning platform for precision agriculture. Novelty: 0.78 | Defensibility: 0.72. Core Technology Differentiation: 6 | Patent Portfolio: 5 | Research Validation: 4 | Product Linkage: 3 | Scalability: 2",
    )


def create_dummy_market_analysis() -> MarketabilityAnalysisResult:
    """Create dummy market analysis result."""
    return MarketabilityAnalysisResult(
        target_market_size="$15B+ global precision agriculture market, growing at 12% CAGR",
        market_growth_potential=0.68,
        customer_pain_points=[
            "Early crop disease detection for wheat, corn, and soybeans",
            "Optimization of irrigation efficiency in water-scarce regions",
            "Automated farm monitoring reducing labor costs",
        ],
        business_model="SaaS subscription with usage-based add-ons (drone surveys, advanced analytics)",
        adoption_barriers=[
            "Farmer technology adoption curve (5-7 year adoption cycle)",
            "Integration complexity with existing farm equipment",
            "Data privacy concerns from agricultural cooperatives",
        ],
        commercial_feasibility_score=0.65,
        evidence=[
            EvidenceItem(
                claim="$15B addressable market in North America alone",
                source_document="AgTech Market Report 2024",
                evidence_type="Market Data",
                confidence=0.82,
                supporting_details="Compound annual growth rate of 12-15% through 2030"
            ),
            EvidenceItem(
                claim="SaaS model proven in precision ag, similar to John Deere Operations Center",
                source_document="Competitive Analysis",
                evidence_type="Market Intelligence",
                confidence=0.90,
                supporting_details="Per-hectare subscription model at $15-25/hectare/year"
            ),
        ],
        missing_information=[
            "Customer acquisition cost and lifetime value data",
            "Time to payback analysis for farmers",
        ],
        summary="Market Growth Potential: 0.68 | Commercial Feasibility: 0.65. Large addressable market with proven SaaS model.",
    )


def create_dummy_impact_analysis() -> ImpactAnalysisResult:
    """Create dummy impact analysis result."""
    return ImpactAnalysisResult(
        environmental_impact=0.72,
        agricultural_impact=0.80,
        sustainability_focus=[
            "Optimized irrigation reducing water usage by 20-30%",
            "Reduced pesticide application through early disease detection",
            "Lower carbon footprint via precision input management",
        ],
        efficiency_improvements=[
            "20% improvement in crop yield through early intervention",
            "30% reduction in water consumption via precision irrigation",
            "25% reduction in pesticide use",
        ],
        yield_improvement_claimed="18-22% yield improvement in field trials (wheat, corn)",
        carbon_reduction_claimed="2.5 tons CO2 equivalent per hectare per year",
        water_saving_claimed="200,000+ gallons water saved per hectare per season",
        evidence=[
            EvidenceItem(
                claim="Field trial results show 20% yield improvement",
                source_document="2023 Field Trial Report - Iowa State University Partnership",
                evidence_type="Validation Report",
                confidence=0.88,
                supporting_details="24-month field trial across 500 hectares in Midwest"
            ),
        ],
        missing_information=[],
        summary="TechFarm impacts agricultural productivity and sustainability. Environmental Impact: 0.72 | Agricultural Impact: 0.80",
    )


def create_dummy_data_moat_analysis() -> DataMoatAnalysisResult:
    """Create dummy data moat analysis result."""
    return DataMoatAnalysisResult(
        has_proprietary_datasets=True,
        dataset_defensibility_score=0.68,
        data_flywheel_potential=0.74,
        sensing_pipeline_uniqueness="Proprietary sensor fusion combining hyperspectral + RGB imaging with weather APIs",
        data_assets_description="Repository of 500K+ labeled crop images from 30+ regions; continuous growth via customer deployments",
        moat_strength_score=0.70,
        evidence=[
            EvidenceItem(
                claim="Growing proprietary dataset of crop disease examples",
                source_document="Data Assets Inventory",
                evidence_type="Data Document",
                confidence=0.80,
                supporting_details="500K+ labeled images collected across North America"
            ),
        ],
        missing_information=[],
        summary="Moderate data moat with potential for strengthening. Moat Strength: 0.70",
    )


def create_dummy_competitor_analysis() -> CompetitorAnalysisResult:
    """Create dummy competitor analysis result."""
    return CompetitorAnalysisResult(
        comparable_competitors=[
            "Taranis (Israel, crop imaging)",
            "Descartes Labs (satellite imagery + ML)",
            "See & Spray (weed detection robotics)",
        ],
        technology_differentiation="TechFarm focuses on real-time ground-based disease detection vs. satellite-only or weed-specific competitors",
        relative_strengths=[
            "Faster real-time detection (hours vs. days with satellite)",
            "Higher accuracy for disease diagnosis (96% vs. 75-85%)",
            "Integrated SaaS platform vs. point solutions",
        ],
        relative_weaknesses=[
            "Requires ground-based hardware (scalability challenge vs. satellite plays)",
            "Limited to ~3-5 year track record vs. competitors with longer history",
            "Regional focus (North America) vs. global competition",
        ],
        competitive_advantage_score=0.69,
        evidence=[
            EvidenceItem(
                claim="TechFarm differentiates on real-time ground detection",
                source_document="Competitive Benchmark Report",
                evidence_type="Competitive Intelligence",
                confidence=0.76,
                supporting_details="Faster feedback loop enables intervention same-day vs competitors"
            ),
        ],
        missing_information=[
            "Customer retention rates vs. competitors",
            "Unit economics comparison",
        ],
        summary="Competitive Advantage: 0.69. Differentiated real-time approach but faces well-funded competitors.",
    )


def create_dummy_investment_decision() -> InvestmentDecision:
    """Create dummy investment decision."""
    return InvestmentDecision(
        recommendation=InvestmentRecommendation.INVEST,
        confidence_score=0.78,
        overall_assessment_score=0.72,
        key_strengths=[
            "Large and growing market ($15B+) with secular tailwinds in climate, food security",
            "Differentiated technology with patent protection and growing data moat",
            "Proven field trial results showing 18-22% yield improvement",
            "Experienced management team with AgTech domain expertise",
            "Strong early customer traction with 3 pilot deployments in progress",
        ],
        key_risks=[
            "Farmer adoption cycle risk: 5-7 year sales cycle may delay revenue scaling",
            "Hardware dependency limits scalability vs. pure software plays",
            "Well-funded competitors (Taranis at $300M+ valuation) could outspend on R&D",
            "Regulatory risk: EU pesticide bans could impact addressable market",
            "Data privacy regulations may constrain cross-region model training",
        ],
        missing_critical_information=[],
        rationale="TechFarm AI presents a compelling investment opportunity with differentiated technology solving a real pain point in precision agriculture. The company benefits from strong tailwinds in food security and climate adaptation. While execution risks exist (adoption cycle, competition), the large TAM and proven field results justify investment at current valuation. Recommend Series A investment of $15-20M.",
        evidence=[],
        evidence_gaps=[
            "Customer acquisition cost and lifetime value metrics",
            "Churn rates and customer retention data",
            "Detailed financial projections and unit economics",
            "Regulatory compliance status across target markets",
        ],
    )


def test_report_generation():
    """Test report generation with dummy data."""
    print("\n" + "="*80)
    print("Testing ReportGenerationAgent with Dummy Data")
    print("="*80 + "\n")

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Create dummy data
    logger.info("Creating dummy data...")
    startup = create_dummy_startup()
    tech_analysis = create_dummy_technology_analysis()
    market_analysis = create_dummy_market_analysis()
    impact_analysis = create_dummy_impact_analysis()
    data_moat_analysis = create_dummy_data_moat_analysis()
    competitor_analysis = create_dummy_competitor_analysis()
    investment_decision = create_dummy_investment_decision()

    print(f"✓ Created dummy startup: {startup.name}")
    print(f"✓ Created technology analysis (novelty: {tech_analysis.novelty_score:.0%})")
    print(f"✓ Created market analysis (growth: {market_analysis.market_growth_potential:.0%})")
    print(f"✓ Created impact analysis (agri impact: {impact_analysis.agricultural_impact:.0%})")
    print(f"✓ Created data moat analysis (moat strength: {data_moat_analysis.moat_strength_score:.0%})")
    print(f"✓ Created competitor analysis (advantage: {competitor_analysis.competitive_advantage_score:.0%})")
    print(f"✓ Created investment decision ({investment_decision.recommendation.value})")

    # Initialize and execute report generation
    logger.info("Initializing ReportGenerationAgent...")
    agent = ReportGenerationAgent()

    logger.info("Executing report generation...")
    evaluation = agent.execute(
        startup=startup,
        tech_analysis=tech_analysis,
        market_analysis=market_analysis,
        impact_analysis=impact_analysis,
        data_moat_analysis=data_moat_analysis,
        competitor_analysis=competitor_analysis,
        investment_decision=investment_decision,
    )

    print("\n✓ Report generation complete!")

    # Verify text report
    print("\n" + "-"*80)
    print("Text Report Content (first 500 chars)")
    print("-"*80)
    print(evaluation.report_content[:500] + "...\n")

    # Verify PDF generation
    output_dir = Path("outputs")
    if output_dir.exists():
        pdf_files = list(output_dir.glob("evaluation_*.pdf"))
        if pdf_files:
            latest_pdf = max(pdf_files, key=os.path.getctime)
            file_size = latest_pdf.stat().st_size
            print("-"*80)
            print("PDF Report")
            print("-"*80)
            print(f"✓ PDF generated: {latest_pdf.name}")
            print(f"  Size: {file_size:,} bytes")
            print(f"  Path: {latest_pdf.absolute()}")
        else:
            print("⚠ No PDF files found in outputs/")
    else:
        print("⚠ outputs/ directory not found")

    # Print summary statistics
    print("\n" + "="*80)
    print("Report Summary Statistics")
    print("="*80)
    print(f"Company: {evaluation.startup.name}")
    print(f"Founded: {evaluation.startup.founded_year}")
    print(f"Stage: {evaluation.startup.stage}")
    print(f"\nEvaluation Scores:")
    print(f"  Technology Novelty:         {evaluation.technology_analysis.novelty_score:.0%}")
    print(f"  Technology Defensibility:   {evaluation.technology_analysis.defensibility_score:.0%}")
    print(f"  Market Growth Potential:    {evaluation.marketability_analysis.market_growth_potential:.0%}")
    print(f"  Commercial Feasibility:     {evaluation.marketability_analysis.commercial_feasibility_score:.0%}")
    print(f"  Environmental Impact:       {evaluation.impact_analysis.environmental_impact:.0%}")
    print(f"  Agricultural Impact:        {evaluation.impact_analysis.agricultural_impact:.0%}")
    print(f"  Data Moat Strength:         {evaluation.data_moat_analysis.moat_strength_score:.0%}")
    print(f"  Competitive Advantage:      {evaluation.competitor_analysis.competitive_advantage_score:.0%}")
    print(f"\nInvestment Decision:")
    print(f"  Recommendation: {evaluation.investment_decision.recommendation.value.upper()}")
    print(f"  Overall Score: {evaluation.investment_decision.overall_assessment_score:.0%}")
    print(f"  Confidence: {evaluation.investment_decision.confidence_score:.0%}")
    print(f"\nKey Strengths: {len(evaluation.investment_decision.key_strengths)}")
    for i, strength in enumerate(evaluation.investment_decision.key_strengths[:3], 1):
        print(f"  {i}. {strength}")
    print(f"\nKey Risks: {len(evaluation.investment_decision.key_risks)}")
    for i, risk in enumerate(evaluation.investment_decision.key_risks[:3], 1):
        print(f"  {i}. {risk}")

    print("\n" + "="*80)
    print("✓ Test Complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_report_generation()
