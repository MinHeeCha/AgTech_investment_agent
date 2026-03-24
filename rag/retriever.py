"""Retriever for RAG-based document retrieval."""

from typing import Optional

try:
    from .chunking import DocumentChunker
    from .embedder import BGEM3Embedder
    from .vectorstore import VectorStore
    from models import RetrievedDocument
except ImportError:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(__file__))
    _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), ".."))
    from chunking import DocumentChunker
    from embedder import BGEM3Embedder
    from vectorstore import VectorStore
    from models import RetrievedDocument


class Retriever:
    """Retrieves relevant documents using BGE-M3 embeddings and FAISS."""

    def __init__(
        self,
        vectorstore: Optional[VectorStore] = None,
        embedder: Optional[BGEM3Embedder] = None,
    ):
        self.vectorstore = vectorstore or VectorStore(embedding_dim=BGEM3Embedder.EMBEDDING_DIM)
        self.embedder = embedder or BGEM3Embedder()
        self.chunker = DocumentChunker()
        self.documents: list[dict] = []

    def add_documents(self, documents: list[dict]):
        """
        Chunk, embed, and index documents into the vector store.

        Args:
            documents: List of dicts with 'content', 'source', and optional 'metadata'
        """
        self.documents.extend(documents)

        chunks = self.chunker.chunk_pdf_documents(documents)
        if not chunks:
            return

        texts = [c.content for c in chunks]
        print(f"Embedding {len(texts)} chunks ...")
        embeddings = self.embedder.embed(texts)

        self.vectorstore.add_chunks_batch(
            contents=texts,
            sources=[c.source_document for c in chunks],
            embeddings=embeddings,
            chunk_indices=[c.chunk_index for c in chunks],
            metadatas=[c.metadata for c in chunks],
        )
        print(f"Indexed {len(chunks)} chunks. Total in store: {self.vectorstore.size()}")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_relevance_score: float = 0.4,
    ) -> list[RetrievedDocument]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Query string
            top_k: Number of results to return
            min_relevance_score: Minimum cosine similarity threshold (0~1)

        Returns:
            List of RetrievedDocument objects sorted by relevance
        """
        query_vec = self.embedder.embed_query(query)
        results = self.vectorstore.search(query_vec, top_k=top_k * 2)

        retrieved_docs = []
        for result in results:
            if result["score"] < min_relevance_score:
                continue

            doc = RetrievedDocument(
                content=result["content"],
                source=result["source"],
                document_type=result["metadata"].get("format", "pdf"),
                relevance_score=result["score"],
                chunk_id=f"{result['source']}_{result['chunk_index']}",
                metadata=result["metadata"],
            )
            retrieved_docs.append(doc)

            if len(retrieved_docs) >= top_k:
                break

        return retrieved_docs

    def retrieve_by_source(self, source: str) -> list[RetrievedDocument]:
        """Retrieve all chunks from a specific source document."""
        retrieved_docs = []
        for chunk in self.vectorstore.vectors:
            if chunk.source_document == source:
                doc = RetrievedDocument(
                    content=chunk.content,
                    source=chunk.source_document,
                    document_type=chunk.metadata.get("format", "pdf"),
                    relevance_score=1.0,
                    chunk_id=f"{chunk.source_document}_{chunk.chunk_index}",
                    metadata=chunk.metadata,
                )
                retrieved_docs.append(doc)
        return retrieved_docs

    def save_index(self, directory: str):
        """Persist the FAISS index and chunk metadata to disk."""
        self.vectorstore.save(directory)

    @classmethod
    def load_index(cls, directory: str, embedder: Optional[BGEM3Embedder] = None) -> "Retriever":
        """
        Load a Retriever from a saved FAISS index (skips re-embedding).

        Args:
            directory: Directory containing index.faiss and chunks.json
            embedder: Optional pre-loaded embedder; one is created if not provided

        Returns:
            Retriever instance ready for querying
        """
        store = VectorStore.load(directory)
        instance = cls.__new__(cls)
        instance.vectorstore = store
        instance.embedder = embedder or BGEM3Embedder()
        instance.chunker = DocumentChunker()
        instance.documents = []
        return instance


if __name__ == "__main__":
    import os

    # Ensure CWD is the project root so relative paths work
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))

    INDEX_DIR = "data/faiss_index"
    TOP_K = 3

    retriever = Retriever.load_index(INDEX_DIR)

    queries = [
        "Regrow 기업 정보",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print("=" * 60)
        docs = retriever.retrieve(query, top_k=TOP_K, min_relevance_score=0.0)
        for i, doc in enumerate(docs, 1):
            print(f"\n[{i}] score={doc.relevance_score:.4f}  {os.path.basename(doc.source)}  chunk#{doc.chunk_id.split('_')[-1]}")
            print("-" * 40)
            print(doc.content[:400])
