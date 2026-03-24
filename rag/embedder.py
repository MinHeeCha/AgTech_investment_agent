"""Embedding model wrapper using BAAI/bge-m3 via sentence-transformers."""

from typing import Union
import numpy as np


class BGEM3Embedder:
    """
    Embedder using BAAI/bge-m3 via sentence-transformers.

    BGE-M3 produces 1024-dim dense vectors. Vectors are L2-normalised
    so that inner product equals cosine similarity (compatible with FAISS IndexFlatIP).
    """

    MODEL_NAME = "BAAI/bge-m3"
    EMBEDDING_DIM = 1024

    def __init__(self, batch_size: int = 16, device: str = None):
        """
        Initialize the BGE-M3 embedding model.

        Args:
            batch_size: Batch size for encoding
            device: Device to run on ('cpu', 'cuda', 'mps'). Auto-detected if None.
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            )

        self.batch_size = batch_size
        self._device = device or self._auto_device()

        print(f"Loading {self.MODEL_NAME} on {self._device} ...")
        self._model = SentenceTransformer(self.MODEL_NAME, device=self._device)
        print("Model loaded.")

    @staticmethod
    def _auto_device() -> str:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"

    def embed(self, texts: Union[str, list[str]]) -> np.ndarray:
        """
        Embed one or more texts. Returns L2-normalised dense vectors (shape: N x 1024).

        Args:
            texts: Single string or list of strings

        Returns:
            numpy array of shape (N, 1024), float32, L2-normalised
        """
        if isinstance(texts, str):
            texts = [texts]

        vectors = self._model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,   # L2 normalise → cosine via inner product
            show_progress_bar=len(texts) > self.batch_size,
            convert_to_numpy=True,
        )
        return vectors.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string. Returns shape (1024,)."""
        return self.embed(query)[0]
