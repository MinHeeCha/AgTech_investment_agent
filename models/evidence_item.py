"""Evidence item data model."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class EvidenceItem:
    """Represents a piece of evidence extracted from documents."""

    claim: str
    source_document: str
    evidence_type: str  # "patent", "research_finding", "customer_testimonial", etc.
    confidence: float = 0.9  # 0.0 to 1.0
    supporting_details: Optional[str] = None

    def __repr__(self) -> str:
        return f"EvidenceItem(claim={self.claim[:50]}..., confidence={self.confidence:.2f})"
