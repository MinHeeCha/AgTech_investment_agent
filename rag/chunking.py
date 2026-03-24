"""Document chunking strategies."""

import re
from dataclasses import dataclass

# PDFs to chunk by 1/3 page; all others are chunked 1 page per chunk
THIRD_PAGE_PDFS = {"agtech_data_moat_16_companies.pdf", "agtech_series_ab.pdf"}


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
    """Handles document chunking by page boundaries."""

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # Page-aware chunking (primary strategy for PDFs)
    # ------------------------------------------------------------------

    def chunk_pdf_documents(self, documents: list[dict]) -> list[Chunk]:
        """
        Chunk PDF documents by page boundaries.

        - agtech_data_moat_16_companies.pdf / agtech_series_ab.pdf → 1/3 page per chunk
        - All other PDFs → 1 full page per chunk

        Args:
            documents: Output of DocumentLoader.load_pdf_file / load_pdf_directory

        Returns:
            List of Chunk objects
        """
        all_chunks = []
        for doc in documents:
            filename = doc.get("metadata", {}).get("file_name", "")
            fractions = 3 if filename in THIRD_PAGE_PDFS else 1
            chunks = self._chunk_by_page(doc, fractions)
            all_chunks.extend(chunks)
        return all_chunks

    def _chunk_by_page(self, doc: dict, fractions: int) -> list[Chunk]:
        """
        Split a document's content into chunks aligned to page boundaries.

        Args:
            doc: Document dict (content has [Page N] markers from loader)
            fractions: Number of chunks per page (1 = full page, 3 = 1/3 page)

        Returns:
            List of Chunk objects
        """
        source = doc["source"]
        base_metadata = doc.get("metadata", {}).copy()

        # Split on [Page N] markers, keeping page numbers
        page_blocks = re.split(r"(\[Page \d+\])", doc["content"])

        # Pair each [Page N] header with its body text
        pages: list[tuple[str, str]] = []
        i = 0
        while i < len(page_blocks):
            block = page_blocks[i].strip()
            if re.fullmatch(r"\[Page \d+\]", block):
                body = page_blocks[i + 1].strip() if i + 1 < len(page_blocks) else ""
                pages.append((block, body))
                i += 2
            else:
                i += 1

        chunks: list[Chunk] = []
        chunk_index = 0

        for page_header, page_body in pages:
            page_num = int(re.search(r"\d+", page_header).group())

            if not page_body:
                continue

            parts = self._split_into_n(page_body, fractions)

            for part_idx, part_text in enumerate(parts):
                if not part_text.strip():
                    continue

                # Prepend page header so each chunk carries its page context
                header = page_header if fractions == 1 else f"{page_header} ({part_idx + 1}/{fractions})"
                content = f"{header}\n{part_text.strip()}"

                metadata = base_metadata.copy()
                metadata["page"] = page_num
                metadata["part"] = part_idx + 1
                metadata["parts_per_page"] = fractions

                chunks.append(
                    Chunk(
                        content=content,
                        source_document=source,
                        chunk_index=chunk_index,
                        start_char=0,
                        end_char=len(content),
                        metadata=metadata,
                    )
                )
                chunk_index += 1

        return chunks

    @staticmethod
    def _split_into_n(text: str, n: int) -> list[str]:
        """
        Split text into n roughly equal parts, breaking at sentence boundaries.

        Args:
            text: Text to split
            n: Number of parts

        Returns:
            List of n text parts
        """
        if n == 1:
            return [text]

        target_len = len(text) // n
        parts = []
        start = 0

        for i in range(n - 1):
            ideal_end = start + target_len
            if ideal_end >= len(text):
                break

            # Search ±20% of target_len around ideal_end for a sentence boundary
            search_range = max(50, target_len // 5)
            search_start = max(start, ideal_end - search_range)
            search_end = min(len(text), ideal_end + search_range)

            # Find the nearest sentence-ending punctuation to ideal_end
            best = ideal_end
            best_dist = search_range
            for j in range(search_start, search_end):
                if text[j] in ".!?\n" and (j + 1 >= len(text) or text[j + 1] in " \n\t"):
                    dist = abs(j - ideal_end)
                    if dist < best_dist:
                        best_dist = dist
                        best = j + 1

            parts.append(text[start:best])
            start = best

        parts.append(text[start:])
        return parts

