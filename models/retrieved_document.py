"""Retrieved document data model."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class RetrievedDocument:
    """Represents a document retrieved during RAG."""

    content: str
    source: str  # URL, file path, etc.
    document_type: str  # "website", "paper", "patent", "news", etc.
    relevance_score: float = 0.0
    chunk_id: Optional[str] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def __repr__(self) -> str:
        return f"RetrievedDocument(source={self.source}, type={self.document_type}, score={self.relevance_score:.2f})"
