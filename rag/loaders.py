"""Document loaders for various file formats."""

import os
from typing import Optional
from pathlib import Path


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
