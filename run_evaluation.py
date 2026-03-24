"""Main entry point and quick start example."""

#!/usr/bin/env python3

import sys
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app import main

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Example startup evaluation
    startup_names = [
        "TechFarm AI",
        "SoilSense Technologies",
        "Regrow",
    ]

    startup_infos = {
        "TechFarm AI": {
            "founded_year": 2021,
            "headquarters": "San Francisco, CA",
            "stage": "Series A",
            "mission": "Democratizing precision agriculture with AI",
            "website": "https://techfarmai.example.com",
        },
        "SoilSense Technologies": {
            "founded_year": 2022,
            "headquarters": "Ames, IA",
            "stage": "Seed",
            "mission": "Real-time soil health monitoring",
            "website": "https://soilsense.example.com",
        },
        "Regrow": {
            "founded_year": 2020,
            "headquarters": "San Francisco, CA",
            "stage": "Series B",
            "name": "Regrow",
            "mission": "Building the agriculture resilience platform for measuring and reducing on-farm emissions",
            "website": "https://www.regrow.ag",
        },
    }

    # Run evaluation
    print("\n" + "="*80)
    print("AgTech Startup Investment Evaluation System")
    print("="*80 + "\n")

    try:
        results = main(
            startup_names,
            startup_infos,
            document_paths=None  # Add your document paths here
        )
        print("\n" + "="*80)
        print("Evaluation completed successfully")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\nError during evaluation: {e}")
        logging.exception("Evaluation failed")
        sys.exit(1)
