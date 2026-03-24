"""Base agent class for all agents."""

from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
import logging

from rag import Retriever
from models import RetrievedDocument


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str, description: str):
        """
        Initialize the agent.

        Args:
            name: Agent name
            description: Agent description
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(self.name)
        self.execution_start_time: Optional[datetime] = None
        self.execution_end_time: Optional[datetime] = None

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the agent's main task."""
        pass

    def log_info(self, message: str):
        """Log an info message."""
        self.logger.info(f"[{self.name}] {message}")

    def log_error(self, message: str):
        """Log an error message."""
        self.logger.error(f"[{self.name}] {message}")

    def log_warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(f"[{self.name}] {message}")

    def start_execution(self):
        """Mark execution start time."""
        self.execution_start_time = datetime.now()
        self.log_info("Execution started")

    def end_execution(self):
        """Mark execution end time."""
        self.execution_end_time = datetime.now()
        if self.execution_start_time:
            duration = (self.execution_end_time - self.execution_start_time).total_seconds()
            self.log_info(f"Execution completed in {duration:.2f} seconds")

    def get_execution_duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.execution_start_time and self.execution_end_time:
            return (self.execution_end_time - self.execution_start_time).total_seconds()
        return None

    def retrieve_documents(self, retriever: Retriever, query: str, 
                          top_k: int = 5) -> list[RetrievedDocument]:
        """
        Retrieve documents using the provided retriever.

        Args:
            retriever: Retriever instance
            query: Search query
            top_k: Number of documents to retrieve

        Returns:
            List of retrieved documents
        """
        self.log_info(f"Retrieving documents for query: {query}")
        docs = retriever.retrieve(query, top_k=top_k)
        self.log_info(f"Retrieved {len(docs)} relevant documents")
        return docs
