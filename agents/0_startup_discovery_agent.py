"""Startup Discovery Agent - Initial stage of investment evaluation."""

from typing import Optional
from models import StartupProfile
from rag import Retriever
from .base_agent import BaseAgent


class StartupDiscoveryAgent(BaseAgent):
    """Agent responsible for identifying and profiling startup candidates."""

    def __init__(self):
        super().__init__(
            name="StartupDiscoveryAgent",
            description="Identifies candidate AgTech startups and gathers core company-level information",
        )

    def execute(self, 
                startup_name: str,
                retriever: Optional[Retriever] = None,
                additional_info: Optional[dict] = None) -> StartupProfile:
        """
        Discover and profile a startup.

        Args:
            startup_name: Name of the startup to discover
            retriever: Optional Retriever for gathering information
            additional_info: Additional information to enrich the profile

        Returns:
            StartupProfile with discovered information
        """
        self.start_execution()

        try:
            self.log_info(f"Discovering startup: {startup_name}")

            # Initialize profile with basic info
            profile = StartupProfile(
                name=startup_name,
                founded_year=2022,  # Default, would be fetched from documents
                headquarters="Unknown",
                description="AgTech startup focused on innovation",
            )

            # If retriever provided, gather additional information
            if retriever:
                docs = self.retrieve_documents(
                    retriever,
                    f"About {startup_name} company background founding",
                    top_k=3
                )

                # Extract information from retrieved documents
                if docs:
                    self.log_info("Retrieved company information documents")
                    # In a real implementation, would parse docs for specific info
                    profile.discovery_source = docs[0].source if docs else None

            # Merge additional information if provided
            if additional_info:
                if "founded_year" in additional_info:
                    profile.founded_year = additional_info["founded_year"]
                if "headquarters" in additional_info:
                    profile.headquarters = additional_info["headquarters"]
                if "website" in additional_info:
                    profile.website = additional_info["website"]
                if "founders" in additional_info:
                    profile.founders = additional_info["founders"]
                if "mission" in additional_info:
                    profile.mission = additional_info["mission"]
                if "stage" in additional_info:
                    profile.stage = additional_info["stage"]

            self.log_info(f"Successfully profiled startup: {profile.name}")

            return profile

        finally:
            self.end_execution()

    def batch_discover(self, startup_names: list[str],
                      retriever: Optional[Retriever] = None) -> list[StartupProfile]:
        """
        Discover multiple startups.

        Args:
            startup_names: List of startup names
            retriever: Optional Retriever

        Returns:
            List of discovered profiles
        """
        self.log_info(f"Discovering {len(startup_names)} startups")
        profiles = []

        for name in startup_names:
            profile = self.execute(name, retriever)
            profiles.append(profile)

        return profiles
