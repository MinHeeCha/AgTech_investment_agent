"""Configuration for the investment evaluation system."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """System configuration."""

    # API Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-3-haiku")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # RAG Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1024"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    RELEVANCE_THRESHOLD: float = float(os.getenv("RELEVANCE_THRESHOLD", "0.5"))

    # Agent Configuration
    MAX_PARALLEL_WORKERS: int = int(os.getenv("MAX_PARALLEL_WORKERS", "4"))
    AGENT_TIMEOUT: int = int(os.getenv("AGENT_TIMEOUT", "300"))

    # Evaluation Configuration
    STRONG_INVEST_THRESHOLD: float = 0.75
    INVEST_THRESHOLD: float = 0.60
    HOLD_THRESHOLD: float = 0.40

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "investment_evaluation.log")

    # Data Configuration
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    RAW_DATA_DIR: str = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR: str = os.path.join(DATA_DIR, "processed")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables."""
        return cls()

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "llm_model": self.LLM_MODEL,
            "embedding_model": self.EMBEDDING_MODEL,
            "chunk_size": self.CHUNK_SIZE,
            "chunk_overlap": self.CHUNK_OVERLAP,
            "top_k_retrieval": self.TOP_K_RETRIEVAL,
            "max_parallel_workers": self.MAX_PARALLEL_WORKERS,
            "log_level": self.LOG_LEVEL,
            "invest_threshold": self.INVEST_THRESHOLD,
            "strong_invest_threshold": self.STRONG_INVEST_THRESHOLD,
        }
