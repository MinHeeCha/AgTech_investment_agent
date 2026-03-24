"""FAISS-based vector store for embeddings and similarity search."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@dataclass
class VectorizedChunk:
    """Chunk with embeddings."""

    content: str
    source_document: str
    chunk_index: int
    embedding: list[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class VectorStore:
    """
    FAISS-based vector store for similarity search.

    Uses IndexFlatIP (inner product) with L2-normalised vectors,
    which is equivalent to cosine similarity.
    """

    def __init__(self, embedding_dim: int = 1024):
        """
        Initialize the FAISS vector store.

        Args:
            embedding_dim: Dimension of embeddings (1024 for BGE-M3)
        """
        if not FAISS_AVAILABLE:
            raise ImportError("faiss-cpu is not installed. Run: pip install faiss-cpu")

        self.embedding_dim = embedding_dim
        self._index = faiss.IndexFlatIP(embedding_dim)
        self._chunks: list[VectorizedChunk] = []

    def add_chunk(
        self,
        chunk_content: str,
        source: str,
        embedding: np.ndarray | list[float],
        chunk_index: int = 0,
        metadata: Optional[dict] = None,
    ):
        """Add a single vectorized chunk to the store."""
        if metadata is None:
            metadata = {}

        vec = self._to_float32_row(embedding)
        self._index.add(vec)

        self._chunks.append(
            VectorizedChunk(
                content=chunk_content,
                source_document=source,
                chunk_index=chunk_index,
                embedding=vec[0].tolist(),
                metadata=metadata,
            )
        )

    def add_chunks_batch(
        self,
        contents: list[str],
        sources: list[str],
        embeddings: np.ndarray,
        chunk_indices: Optional[list[int]] = None,
        metadatas: Optional[list[dict]] = None,
    ):
        """
        Add many chunks at once (faster than add_chunk in a loop).

        Args:
            contents: List of text contents
            sources: List of source document paths
            embeddings: (N, dim) float32 numpy array, L2-normalised
            chunk_indices: Optional list of per-chunk indices
            metadatas: Optional list of metadata dicts
        """
        n = len(contents)
        if chunk_indices is None:
            chunk_indices = list(range(n))
        if metadatas is None:
            metadatas = [{}] * n

        vecs = np.array(embeddings, dtype=np.float32)
        if vecs.ndim == 1:
            vecs = vecs.reshape(1, -1)

        self._index.add(vecs)

        for i in range(n):
            self._chunks.append(
                VectorizedChunk(
                    content=contents[i],
                    source_document=sources[i],
                    chunk_index=chunk_indices[i],
                    embedding=vecs[i].tolist(),
                    metadata=metadatas[i],
                )
            )

    def search(self, query_embedding: np.ndarray | list[float], top_k: int = 5) -> list[dict]:
        """
        Find the most similar chunks to a query.

        Args:
            query_embedding: Query embedding vector (1D array or list)
            top_k: Number of top results to return

        Returns:
            List of dicts with keys: content, source, chunk_index, score, metadata
        """
        if self._index.ntotal == 0:
            return []

        vec = self._to_float32_row(query_embedding)
        scores, indices = self._index.search(vec, min(top_k, self._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk = self._chunks[idx]
            results.append(
                {
                    "content": chunk.content,
                    "source": chunk.source_document,
                    "chunk_index": chunk.chunk_index,
                    "score": float(score),
                    "metadata": chunk.metadata,
                }
            )
        return results

    def save(self, directory: str):
        """
        Persist the FAISS index and chunk metadata to disk.

        Args:
            directory: Directory to save files into
        """
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self._index, str(path / "index.faiss"))

        meta = [
            {
                "content": c.content,
                "source_document": c.source_document,
                "chunk_index": c.chunk_index,
                "metadata": c.metadata,
            }
            for c in self._chunks
        ]
        with open(path / "chunks.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        print(f"Saved {self._index.ntotal} vectors to {directory}")

    @classmethod
    def load(cls, directory: str) -> "VectorStore":
        """
        Load a VectorStore from disk.

        Args:
            directory: Directory containing index.faiss and chunks.json

        Returns:
            Loaded VectorStore instance
        """
        if not FAISS_AVAILABLE:
            raise ImportError("faiss-cpu is not installed. Run: pip install faiss-cpu")

        path = Path(directory)
        index = faiss.read_index(str(path / "index.faiss"))

        with open(path / "chunks.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        dim = index.d
        store = cls(embedding_dim=dim)
        store._index = index
        store._chunks = [
            VectorizedChunk(
                content=m["content"],
                source_document=m["source_document"],
                chunk_index=m["chunk_index"],
                metadata=m["metadata"],
            )
            for m in meta
        ]
        print(f"Loaded {index.ntotal} vectors from {directory}")
        return store

    def clear(self):
        """Clear all vectors from the store."""
        self._index.reset()
        self._chunks = []

    def size(self) -> int:
        """Return the number of vectors in the store."""
        return self._index.ntotal

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_float32_row(self, vec: np.ndarray | list[float]) -> np.ndarray:
        """Convert any vector input to a (1, dim) float32 numpy array."""
        arr = np.array(vec, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        return arr

    # Legacy compatibility – kept so existing tests don't break
    @property
    def vectors(self) -> list[VectorizedChunk]:
        return self._chunks

    def add_chunks(self, chunks: list[dict]):
        """Legacy batch-add interface (dict-based)."""
        for chunk in chunks:
            self.add_chunk(
                chunk["content"],
                chunk["source"],
                chunk.get("embedding", [0.0] * self.embedding_dim),
                chunk.get("chunk_index", 0),
                chunk.get("metadata"),
            )
