"""Document chunking strategies."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class Chunk:
    """Represents a chunk of text from a document."""

    content: str
    source_document: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DocumentChunker:
    """Handles document chunking with various strategies."""

    def __init__(
        self,
        chunk_size: int = 1024,
        overlap: int = 100,
        preserve_sentences: bool = True,
    ):
        """
        Initialize the document chunker.

        Args:
            chunk_size: Target size of chunks in characters
            overlap: Number of overlapping characters between chunks
            preserve_sentences: If True, avoid breaking mid-sentence
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.preserve_sentences = preserve_sentences

    def chunk_text(
        self, text: str, source_document: str, metadata: Optional[dict] = None
    ) -> list[Chunk]:
        """
        Chunk a document into smaller pieces.

        Args:
            text: Document text to chunk
            source_document: Source identifier for the document
            metadata: Additional metadata for chunks

        Returns:
            List of Chunk objects
        """
        if metadata is None:
            metadata = {}

        chunks = []
        start_idx = 0
        chunk_index = 0

        while start_idx < len(text):
            # Calculate end position
            end_idx = min(start_idx + self.chunk_size, len(text))

            # If we're not at the end and need to preserve sentences,
            # find the last sentence boundary
            if (
                end_idx < len(text)
                and self.preserve_sentences
                and end_idx > start_idx + 100
            ):
                # Find the last period, question mark, or exclamation
                for i in range(end_idx, start_idx + 100, -1):
                    if text[i] in ".!?":
                        end_idx = i + 1
                        break

            # Extract chunk
            chunk_text = text[start_idx : end_idx].strip()

            if chunk_text:  # Only create chunks with content
                chunk = Chunk(
                    content=chunk_text,
                    source_document=source_document,
                    chunk_index=chunk_index,
                    start_char=start_idx,
                    end_char=end_idx,
                    metadata=metadata.copy(),
                )
                chunks.append(chunk)
                chunk_index += 1

            # Move to next chunk with overlap
            start_idx = max(start_idx + self.chunk_size - self.overlap, end_idx)

            if start_idx >= len(text):
                break

        return chunks

    def chunk_documents(
        self, documents: list[dict]
    ) -> list[Chunk]:
        """
        Chunk multiple documents.

        Args:
            documents: List of document dicts with 'content' and 'source' keys

        Returns:
            List of Chunk objects from all documents
        """
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_text(
                doc["content"], doc["source"], doc.get("metadata", {})
            )
            all_chunks.extend(chunks)
        return all_chunks
