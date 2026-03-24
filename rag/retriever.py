"""Retriever for RAG-based document retrieval."""

from typing import Optional
from models import RetrievedDocument
from .vectorstore import VectorStore
from .chunking import DocumentChunker


class Retriever:
    """Retrieves relevant documents for a query."""

    def __init__(
        self,
        vectorstore: Optional[VectorStore] = None,
        chunk_size: int = 1024,
    ):
        """
        Initialize the retriever.

        Args:
            vectorstore: Optional VectorStore instance
            chunk_size: Size of chunks for the chunker
        """
        self.vectorstore = vectorstore or VectorStore()
        self.chunker = DocumentChunker(chunk_size=chunk_size)
        self.documents = []

    def add_documents(self, documents: list[dict]):
        """
        Add documents to the retriever's index.

        Args:
            documents: List of documents with 'content' and 'source'
        """
        self.documents.extend(documents)

        # Chunk the documents
        chunks = self.chunker.chunk_documents(documents)

        # Here you would normally embed chunks using an embedding model
        # For now, we'll create dummy embeddings
        for chunk in chunks:
            dummy_embedding = self._create_dummy_embedding(chunk.content)
            self.vectorstore.add_chunk(
                chunk.content,
                chunk.source_document,
                dummy_embedding,
                chunk.chunk_index,
                chunk.metadata,
            )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_relevance_score: float = 0.5,
    ) -> list[RetrievedDocument]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Query string
            top_k: Number of top results to return
            min_relevance_score: Minimum relevance score threshold

        Returns:
            List of RetrievedDocument objects
        """
        # Create query embedding
        query_embedding = self._create_dummy_embedding(query)

        # Search vector store
        results = self.vectorstore.search(query_embedding, top_k=top_k * 2)

        # Filter by relevance score
        retrieved_docs = []
        for result in results:
            if result["score"] >= min_relevance_score:
                doc = RetrievedDocument(
                    content=result["content"],
                    source=result["source"],
                    document_type=result["metadata"].get("format", "unknown"),
                    relevance_score=result["score"],
                    chunk_id=f"{result['source']}_{result['chunk_index']}",
                    metadata=result["metadata"],
                )
                retrieved_docs.append(doc)

            if len(retrieved_docs) >= top_k:
                break

        return retrieved_docs

    def retrieve_by_source(self, source: str) -> list[RetrievedDocument]:
        """
        Retrieve documents from a specific source.

        Args:
            source: Source identifier (URL, file path, etc.)

        Returns:
            List of RetrievedDocument objects
        """
        retrieved_docs = []
        for vec_chunk in self.vectorstore.vectors:
            if vec_chunk.source_document == source:
                doc = RetrievedDocument(
                    content=vec_chunk.content,
                    source=vec_chunk.source_document,
                    document_type=vec_chunk.metadata.get("format", "unknown"),
                    relevance_score=1.0,
                    chunk_id=f"{vec_chunk.source_document}_{vec_chunk.chunk_index}",
                    metadata=vec_chunk.metadata,
                )
                retrieved_docs.append(doc)
        return retrieved_docs

    @staticmethod
    def _create_dummy_embedding(text: str) -> list[float]:
        """
        Create a dummy embedding for demo purposes.

        In production, this would use a real embedding model like BERT, Ada, etc.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Simple hash-based embedding for demo purposes
        import hashlib

        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()

        # Convert hex to float values
        embedding = []
        for i in range(0, len(hash_hex), 4):
            chunk = hash_hex[i : i + 4]
            value = int(chunk, 16) / 65535.0 - 0.5
            embedding.append(value)

        # Pad to dimension 768
        while len(embedding) < 768:
            embedding.append(0.0)

        return embedding[:768]
