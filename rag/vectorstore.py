"""Vector store for embeddings and similarity search."""

from typing import Optional
from dataclasses import dataclass, field
import math


@dataclass
class VectorizedChunk:
    """Chunk with embeddings."""

    content: str
    source_document: str
    chunk_index: int
    embedding: list[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class VectorStore:
    """In-memory vector store for similarity search."""

    def __init__(self, embedding_dim: int = 768):
        """
        Initialize the vector store.

        Args:
            embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
        self.vectors: list[VectorizedChunk] = []

    def add_chunk(self, chunk_content: str, source: str, embedding: list[float],
                  chunk_index: int = 0, metadata: Optional[dict] = None):
        """
        Add a vectorized chunk to the store.

        Args:
            chunk_content: Text content of the chunk
            source: Source document identifier
            embedding: Embedding vector
            chunk_index: Index of chunk within document
            metadata: Additional metadata
        """
        if metadata is None:
            metadata = {}

        vec_chunk = VectorizedChunk(
            content=chunk_content,
            source_document=source,
            chunk_index=chunk_index,
            embedding=embedding,
            metadata=metadata,
        )
        self.vectors.append(vec_chunk)

    def add_chunks(self, chunks: list[dict]):
        """
        Add multiple chunks at once.

        Args:
            chunks: List of chunk dicts with 'content', 'source', 'embedding' keys
        """
        for chunk in chunks:
            self.add_chunk(
                chunk["content"],
                chunk["source"],
                chunk.get("embedding", []),
                chunk.get("chunk_index", 0),
                chunk.get("metadata"),
            )

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """
        Find the most similar chunks to a query.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return

        Returns:
            List of similar chunks with scores
        """
        if not self.vectors:
            return []

        # Calculate cosine similarity with all vectors
        similarities = []
        for vec_chunk in self.vectors:
            similarity = self._cosine_similarity(query_embedding, vec_chunk.embedding)
            similarities.append(
                {
                    "content": vec_chunk.content,
                    "source": vec_chunk.source_document,
                    "chunk_index": vec_chunk.chunk_index,
                    "score": similarity,
                    "metadata": vec_chunk.metadata,
                }
            )

        # Sort by score and return top_k
        similarities.sort(key=lambda x: x["score"], reverse=True)
        return similarities[:top_k]

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def clear(self):
        """Clear all vectors from the store."""
        self.vectors = []

    def size(self) -> int:
        """Get the number of vectors in the store."""
        return len(self.vectors)
