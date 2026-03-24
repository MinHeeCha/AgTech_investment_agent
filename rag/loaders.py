"""Document loaders for various file formats."""

import os
from typing import Optional
from pathlib import Path

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class DocumentLoader:
    """Load documents from various sources."""

    @staticmethod
    def load_text_file(file_path: str) -> dict:
        """
        Load a plain text file.

        Args:
            file_path: Path to the text file

        Returns:
            Dict with 'content' and 'source' keys
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {"content": content, "source": file_path, "format": "text"}

    @staticmethod
    def load_markdown_file(file_path: str) -> dict:
        """
        Load a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            Dict with 'content' and 'source' keys
        """
        return DocumentLoader.load_text_file(file_path)

    @staticmethod
    def load_directory(
        directory: str, pattern: str = "*.txt"
    ) -> list[dict]:
        """
        Load all files matching a pattern from a directory.

        Args:
            directory: Path to the directory
            pattern: File pattern to match (e.g., '*.txt', '*.md')

        Returns:
            List of documents
        """
        documents = []
        path = Path(directory)

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        for file_path in path.glob(pattern):
            if file_path.is_file():
                try:
                    doc = DocumentLoader.load_text_file(str(file_path))
                    documents.append(doc)
                except Exception as e:
                    print(f"Warning: Could not load {file_path}: {e}")

        return documents

    @staticmethod
    def _table_to_markdown(table: list[list]) -> str:
        """Convert a pdfplumber table (list of rows) to markdown table format."""
        rows = []
        for row in table:
            # Replace None cells with empty string
            cleaned = [cell.strip() if cell else "" for cell in row]
            rows.append("| " + " | ".join(cleaned) + " |")

        if not rows:
            return ""

        # Insert header separator after first row
        col_count = len(table[0])
        separator = "| " + " | ".join(["---"] * col_count) + " |"
        rows.insert(1, separator)

        return "\n".join(rows)

    @staticmethod
    def load_pdf_file(file_path: str) -> dict:
        """
        Load a PDF file using pdfplumber, preserving table structure as markdown.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dict with 'content', 'source', 'format', and 'metadata' keys
        """
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber is not installed. Run: pip install pdfplumber")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        page_texts = []

        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract tables on this page (bounding boxes to track positions)
                tables = page.find_tables()
                table_bboxes = [t.bbox for t in tables]

                # Build a map of table bbox -> markdown string
                rendered_tables: dict[tuple, str] = {}
                for table_obj in tables:
                    data = table_obj.extract()
                    if data:
                        md = DocumentLoader._table_to_markdown(data)
                        if md:
                            rendered_tables[table_obj.bbox] = md

                # Extract plain text, excluding table regions to avoid duplication
                words = page.extract_words()
                table_free_words = []
                for word in words:
                    in_table = any(
                        bbox[0] <= word["x0"] and word["x1"] <= bbox[2]
                        and bbox[1] <= word["top"] and word["bottom"] <= bbox[3]
                        for bbox in table_bboxes
                    )
                    if not in_table:
                        table_free_words.append(word["text"])

                plain_text = " ".join(table_free_words).strip()

                # Assemble page content: plain text + markdown tables
                parts = []
                if plain_text:
                    parts.append(plain_text)
                for md_table in rendered_tables.values():
                    parts.append(md_table)

                if parts:
                    page_content = f"[Page {page_num}]\n" + "\n\n".join(parts)
                    page_texts.append(page_content)

        content = "\n\n".join(page_texts)

        return {
            "content": content,
            "source": file_path,
            "format": "pdf",
            "metadata": {
                "file_name": Path(file_path).name,
                "total_pages": total_pages,
            },
        }

    @staticmethod
    def load_pdf_directory(directory: str) -> list[dict]:
        """
        Load all PDF files from a directory.

        Args:
            directory: Path to the directory

        Returns:
            List of documents
        """
        documents = []
        path = Path(directory)

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        for file_path in sorted(path.glob("*.pdf")):
            if file_path.is_file():
                try:
                    doc = DocumentLoader.load_pdf_file(str(file_path))
                    documents.append(doc)
                    print(f"Loaded: {file_path.name} ({doc['metadata']['total_pages']} pages)")
                except Exception as e:
                    print(f"Warning: Could not load {file_path.name}: {e}")

        return documents

    @staticmethod
    def load_from_urls(urls: list[str]) -> list[dict]:
        """
        Load documents from URLs (placeholder for implementation).

        Args:
            urls: List of URLs to load

        Returns:
            List of documents
        """
        # This is a placeholder - actual implementation would use requests
        # and BeautifulSoup or similar
        documents = []
        for url in urls:
            documents.append(
                {
                    "content": f"Placeholder content from {url}",
                    "source": url,
                    "format": "web",
                }
            )
        return documents
