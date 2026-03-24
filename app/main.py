"""Main application for AgTech investment evaluation."""

import logging
import json
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv
from app.config import Config
from app.orchestrator import AgentOrchestrator
from rag import Retriever, DocumentLoader

# Load environment variables from .env if present.
load_dotenv()


def setup_logging(config: Config):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler(),
        ],
    )


def initialize_retriever(logger: logging.Logger) -> Retriever:
    """
    Initialize retriever from persisted FAISS index if available.

    Falls back to an empty in-memory retriever when index files are missing
    or loading fails.
    """
    index_dir = Path(__file__).resolve().parent.parent / "data" / "faiss_index"
    index_file = index_dir / "index.faiss"
    chunks_file = index_dir / "chunks.json"

    if index_file.exists() and chunks_file.exists():
        try:
            retriever = Retriever.load_index(str(index_dir))
            logger.info(f"Loaded FAISS index from {index_dir}")
            return retriever
        except Exception as e:
            logger.warning(f"Failed to load FAISS index from {index_dir}: {e}")

    logger.info("FAISS index not found; starting with empty retriever")
    return Retriever()


def main(startup_names: Optional[List[str]] = None,
         startup_infos: Optional[dict] = None,
         document_paths: Optional[List[str]] = None):
    """
    Main evaluation pipeline.

    Args:
        startup_names: Deprecated. Step0 discovery is used instead.
        startup_infos: Deprecated. Step0 discovery is used instead.
        document_paths: Optional paths to documents for RAG
    """
    # Setup configuration and logging
    config = Config.from_env()
    setup_logging(config)
    logger = logging.getLogger("MainApp")

    logger.info("AgTech Investment Evaluation System Starting")
    logger.info(f"Configuration: {config.to_dict()}")

    # Initialize retriever (prefer persisted FAISS index)
    retriever = initialize_retriever(logger)

    # Load documents if provided
    if document_paths:
        logger.info(f"Loading documents from {len(document_paths)} paths")
        loader = DocumentLoader()
        for path in document_paths:
            if Path(path).is_file():
                try:
                    doc = loader.load_text_file(path)
                    retriever.add_documents([doc])
                    logger.info(f"Loaded document: {path}")
                except Exception as e:
                    logger.warning(f"Failed to load document {path}: {e}")
            elif Path(path).is_dir():
                try:
                    docs = loader.load_directory(path, "*.txt")
                    retriever.add_documents(docs)
                    logger.info(f"Loaded {len(docs)} documents from {path}")
                except Exception as e:
                    logger.warning(f"Failed to load directory {path}: {e}")

    # Initialize orchestrator
    orchestrator = AgentOrchestrator(retriever, config.MAX_PARALLEL_WORKERS)
    logger.info(f"Orchestrator initialized with workflow: {orchestrator.get_workflow_summary()}")

    # Create output directory
    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Evaluate startups from Step 0 discovery
    if startup_names:
        logger.warning(
            "startup_names input is ignored. Running Step0 discovery via orchestrator.evaluate_all()."
        )
    if startup_infos:
        logger.warning(
            "startup_infos input is ignored. Running Step0 discovery via orchestrator.evaluate_all()."
        )

    logger.info("Starting evaluation from Step0 discovery")
    results = orchestrator.evaluate_all()

    # Save results
    logger.info(f"Saving {len(results)} evaluation results")
    for result in results:
        # Save detailed report
        report_file = output_dir / f"{result.startup.name}_evaluation_report.txt"
        with open(report_file, "w") as f:
            f.write(result.report_content)
        logger.info(f"Saved report: {report_file}")

        # Save JSON summary
        json_file = output_dir / f"{result.startup.name}_evaluation_summary.json"
        with open(json_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        logger.info(f"Saved summary: {json_file}")

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 80)

    for result in results:
        logger.info(f"\n{result.startup.name}:")
        logger.info(f"  Decision: {result.investment_decision.recommendation.value}")
        logger.info(f"  Score: {result.investment_decision.overall_assessment_score:.2%}")
        logger.info(f"  Confidence: {result.investment_decision.confidence_score:.2%}")

    logger.info("\n" + "=" * 80)
    logger.info("Evaluation pipeline complete")

    return results


if __name__ == "__main__":
    # Run evaluation from Step0 startup discovery.
    results = main()
