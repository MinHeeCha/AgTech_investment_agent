"""Startup profile data model."""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class StartupProfile:
    """Represents a startup company profile."""

    # Core identification
    name: str
    founded_year: int
    headquarters: str
    website: Optional[str] = None

    # Business information
    description: str = ""
    mission: Optional[str] = None
    founders: list[str] = field(default_factory=list)

    # Market information
    industry: Optional[str] = None
    target_markets: list[str] = field(default_factory=list)
    stage: Optional[str] = None  # Seed, Series A, Series B, etc.

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    discovery_source: Optional[str] = None

    def __repr__(self) -> str:
        return f"StartupProfile(name={self.name}, founded={self.founded_year}, stage={self.stage})"
