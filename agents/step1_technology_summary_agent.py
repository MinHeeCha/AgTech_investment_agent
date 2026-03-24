"""Technology Summary Agent - Analyzes core technology using RAG-based evidence retrieval."""

import re
from typing import Optional
from models import TechnologyAnalysisResult, EvidenceItem, StartupProfile
from rag import Retriever
from .base_agent import BaseAgent


class TechnologySummaryAgent(BaseAgent):
    """Agent responsible for analyzing startup technology and innovation via criterion-based evaluation."""

    def __init__(self):
        super().__init__(
            name="TechnologySummaryAgent",
            description="Evaluates core technology, patents, research validation, and scalability using RAG-based retrieval",
        )

    def execute(self, startup: StartupProfile, 
               retriever: Optional[Retriever] = None) -> TechnologyAnalysisResult:
        """
        Evaluate startup technology and originality on a 20-point scale.
        
        Scoring Criteria (20 points total):
        - Core Technology Differentiation (6 points)
        - Patent Portfolio (5 points)
        - Research / Technical Validation (4 points)
        - Product Linkage / Commercialization (3 points)
        - Scalability / Applicability Breadth (2 points)

        Args:
            startup: Startup profile to analyze
            retriever: Optional Retriever for gathering technical evidence

        Returns:
            TechnologyAnalysisResult with detailed evidence-based scoring
        """
        self.start_execution()

        try:
            self.log_info(f"Evaluating technology for {startup.name}")

            result = TechnologyAnalysisResult(
                core_technology="",
                novelty_score=0.0,
                defensibility_score=0.0,
            )

            # If no retriever, return minimal result
            if not retriever:
                result.missing_information.append(
                    "Retriever not provided; cannot perform technology evaluation"
                )
                result.summary = "Technology evaluation incomplete: no retriever provided."
                self.log_info(f"Technology analysis skipped for {startup.name} (no retriever)")
                return result

            # Step 1: Build multiple retrieval queries targeting different evidence types
            queries = self._build_multiple_queries(startup)
            self.log_info(f"Executing {len(queries)} retrieval queries for {startup.name}")

            # Step 2: Retrieve documents across multiple query strategies
            all_docs = []
            for query in queries:
                docs = self.retrieve_documents(retriever, query, top_k=5)
                all_docs.extend(docs)

            # Step 3: Deduplicate documents
            unique_docs = self._deduplicate_documents(all_docs)
            self.log_info(f"Retrieved {len(unique_docs)} unique documents for {startup.name}")

            if not unique_docs:
                result.missing_information.append(
                    "No technical documents found in retriever for this startup"
                )
                result.summary = "Technology evaluation incomplete: no supporting documents found."
                self.log_info(f"No retrievals found for {startup.name}")
                return result

            # Step 4: Categorize documents by type
            doc_categories = self._categorize_documents(unique_docs, startup.name)

            # Step 5: Populate straightforward result fields
            self._populate_patents(result, doc_categories)
            self._populate_research_papers(result, doc_categories)
            self._populate_evidence_items(result, unique_docs, startup.name)
            self._extract_and_set_keywords(result, unique_docs)

            # Step 6: Synthesize core technology description from evidence
            result.core_technology = self._synthesize_core_technology(
                unique_docs, startup.name
            )

            # Step 7: Score each of the 5 evaluation criteria
            scores = self._compute_criterion_scores(
                doc_categories, unique_docs, startup.name, result
            )

            # Step 8: Compute normalized novelty and defensibility scores
            # novelty_score (0-1) represents: core_differentiation + research_validation strength
            # defensibility_score (0-1) represents: patent strength + product linkage + validation
            max_novelty_related = 6 + 4  # core_diff(6) + research_validation(4)
            max_defensibility_related = 5 + 3 + 4  # patents(5) + linkage(3) + validation(4)

            novelty_raw = (
                scores.get("core_technology_differentiation", 0) +
                scores.get("research_validation", 0)
            )
            defensibility_raw = (
                scores.get("patent_portfolio", 0) +
                scores.get("product_linkage", 0) +
                scores.get("research_validation", 0)
            )

            result.novelty_score = self._clamp(novelty_raw / max_novelty_related)
            result.defensibility_score = self._clamp(defensibility_raw / max_defensibility_related)

            # Step 9: Build comprehensive summary with criterion breakdown
            total_score = sum(scores.values())
            criterion_summary = self._build_criterion_summary(scores)
            
            result.summary = (
                f"Technology evaluation: {total_score}/20 points. "
                f"Novelty: {result.novelty_score:.2f} | Defensibility: {result.defensibility_score:.2f}. "
                f"{criterion_summary}"
            )

            # Step 10: Add missing information indicators based on low/zero scores
            self._add_missing_information_notes(result, scores)

            self.log_info(f"Technology analysis complete for {startup.name}: {total_score}/20 points")

            return result

        finally:
            self.end_execution()

    def _build_multiple_queries(self, startup: StartupProfile) -> list[str]:
        """
        Build multiple search queries targeting different technical evidence sources.
        
        Returns:
            list of query strings covering patents, papers, validation, and product features
        """
        queries = [
            f"{startup.name} patent PCT international patent application",
            f"{startup.name} research paper published whitepaper journal conference",
            f"{startup.name} technology validation field trial experimental results",
            f"{startup.name} product features technical specifications platform",
            f"{startup.name} proprietary algorithm method innovation breakthrough",
        ]
        return queries

    @staticmethod
    def _deduplicate_documents(docs: list) -> list:
        """Remove duplicate documents by source identifier."""
        seen = set()
        unique = []
        for doc in docs:
            source = getattr(doc, 'source', None) or getattr(doc, 'id', None)
            if source and source not in seen:
                seen.add(source)
                unique.append(doc)
            elif not source and doc not in unique:
                unique.append(doc)
        return unique

    @staticmethod
    def _company_snippets(text: str, company_name: str, window: int = 250) -> list[str]:
        """
        Extract short snippets around company name mentions.
        
        Mirrors marketability agent approach to avoid cross-company contamination.
        """
        if not text or not company_name:
            return []

        patterns = [re.escape(company_name.strip())]
        tokens = re.split(r"[^a-z0-9]+", company_name.lower())
        patterns.extend(
            rf"\b{re.escape(token)}\b" for token in tokens if len(token) >= 3
        )

        snippets = []
        seen = set()
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                start = max(0, match.start() - window)
                end = min(len(text), match.end() + window)
                snippet = text[start:end].strip()
                if snippet and snippet not in seen:
                    seen.add(snippet)
                    snippets.append(snippet)
        return snippets[:3]

    def _categorize_documents(self, docs: list, company_name: str) -> dict:
        """
        Categorize documents by evidence type: patents, papers, whitepapers, product docs, validation.
        
        Returns:
            dict with keys: 'patents', 'research_papers', 'whitepapers', 'product_docs', 'validation_docs', 'other'
        """
        categories = {
            "patents": [],
            "research_papers": [],
            "whitepapers": [],
            "product_docs": [],
            "validation_docs": [],
            "other": [],
        }

        for doc in docs:
            content = getattr(doc, 'content', "") or ""
            doc_type = getattr(doc, 'document_type', "").lower()
            source = getattr(doc, 'source', "").lower()

            # Patent classification
            if (
                "patent" in doc_type or "patent" in source or
                "pct" in doc_type or "pct" in source
            ):
                categories["patents"].append(doc)
            # Research paper classification
            elif any(
                x in doc_type for x in ["paper", "research", "publication", "journal", "conference", "arxiv"]
            ) or any(
                x in source for x in ["arxiv", "ieee", "acm", "springer", "elsevier", "journal"]
            ):
                categories["research_papers"].append(doc)
            # Whitepaper / technical validation
            elif (
                "whitepaper" in doc_type or "whitepaper" in source or
                "technical report" in doc_type or
                any(x in content.lower() for x in ["field trial", "experiment", "validation", "benchmark", "tested"])
            ):
                categories["whitepapers"].append(doc)
            # Product / commercial documentation
            elif (
                "product" in doc_type or "product" in source or
                "website" in doc_type or
                any(x in content.lower() for x in ["feature", "functionality", "capability", "offering", "product"])
            ):
                categories["product_docs"].append(doc)
            # Validation evidence (field trials, experiments, verified results)
            elif any(
                x in content.lower() for x in ["verified", "tested", "trial", "experimental", "outcome", "result"]
            ):
                categories["validation_docs"].append(doc)
            else:
                categories["other"].append(doc)

        return categories

    def _populate_patents(self, result: TechnologyAnalysisResult, doc_categories: dict) -> None:
        """Extract patent sources from categorized patent documents."""
        for doc in doc_categories["patents"]:
            source = getattr(doc, 'source', "Unknown")
            if source not in result.patents:
                result.patents.append(source)

    def _populate_research_papers(self, result: TechnologyAnalysisResult, doc_categories: dict) -> None:
        """Extract research paper sources from categorized paper documents."""
        for doc in doc_categories["research_papers"]:
            source = getattr(doc, 'source', "Unknown")
            if source not in result.research_papers:
                result.research_papers.append(source)

    def _populate_evidence_items(self, result: TechnologyAnalysisResult, docs: list, company_name: str) -> None:
        """
        Create evidence items from retrieved documents with company-specific snippets.
        
        Mirrors marketability agent's evidence construction pattern.
        """
        for doc in docs[:6]:  # Limit to top 6 documents
            content = getattr(doc, 'content', "") or ""
            source = getattr(doc, 'source', "Unknown")
            relevance = getattr(doc, 'relevance_score', 0.5)
            doc_type = getattr(doc, 'document_type', "document").title()

            # Extract company-specific snippet if available
            snippets = self._company_snippets(content, company_name, window=200)
            supporting_text = (
                snippets[0][:200] if snippets
                else content[:200] if content
                else "No summary available"
            )

            evidence = EvidenceItem(
                claim=f"{doc_type} from {source}",
                source_document=source,
                evidence_type=doc_type,
                confidence=relevance,
                supporting_details=supporting_text
            )
            result.evidence.append(evidence)

    def _extract_and_set_keywords(self, result: TechnologyAnalysisResult, docs: list) -> None:
        """Extract technical keywords dynamically from retrieved documents."""
        keywords = self._extract_technical_keywords(docs)
        result.technical_keywords = keywords

    @staticmethod
    def _extract_technical_keywords(docs: list) -> list[str]:
        """
        Extract technical keywords from document content.
        
        Returns:
            list of up to 8 relevant technical terms found in documents
        """
        keywords_set = set()
        
        # AgTech-relevant technology patterns
        tech_patterns = {
            "ai": r"\b(ai|artificial intelligence|machine learning|neural|deep learning)\b",
            "iot": r"\b(iot|sensor|embedded|wireless|telemetry)\b",
            "precision": r"\b(precision|accuracy|optimization|optimize)\b",
            "imaging": r"\b(imaging|vision|satellite|drone|uav|hyperspectral)\b",
            "biology": r"\b(biology|microbe|microbiome|enzyme|protein|dna)\b",
            "data": r"\b(analytics|prediction|forecasting|model|algorithm|data)\b",
            "robotics": r"\b(robot|robotic|automation|autonomous)\b",
            "weather": r"\b(weather|climate|environmental|soil|moisture|water)\b",
        }

        for doc in docs[:5]:
            content = (getattr(doc, 'content', "") or "").lower()
            if not content:
                continue

            for tech, pattern in tech_patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    keywords_set.add(tech)

        return list(keywords_set)[:8]

    def _synthesize_core_technology(self, docs: list, company_name: str) -> str:
        """
        Synthesize core technology description from retrieved documents.
        
        Prefers explicit proprietary/novel technology descriptions over generic summaries.
        """
        if not docs:
            return "Technology information not available in retrieved documents."

        tech_signals = []
        
        # Look for explicit technology descriptors in top documents
        for doc in docs[:3]:
            content = getattr(doc, 'content', "") or ""
            snippets = self._company_snippets(content, company_name, window=250)
            
            for snippet in snippets:
                snippet_lower = snippet.lower()
                # Prefer descriptions containing technology assertions
                if any(
                    x in snippet_lower for x in ["proprietary", "novel", "unique", "patented", "invented"]
                ):
                    tech_signals.append(snippet[:200])
                    break

        if tech_signals:
            return tech_signals[0]

        # Fallback: use first document's content as summary
        first_doc_content = getattr(docs[0], 'content', "") or ""
        if first_doc_content:
            return first_doc_content[:250]

        return "Technology details available in retrieved documents; exact characterization pending review."

    def _compute_criterion_scores(
        self,
        doc_categories: dict,
        all_docs: list,
        company_name: str,
        result: TechnologyAnalysisResult
    ) -> dict:
        """
        Score all 5 technology evaluation criteria and return raw point scores.
        
        Returns:
            dict with criterion: score pairs for all 5 criteria totaling 20 points
        """
        scores = {}

        # Criterion 1: Core Technology Differentiation (6 points max)
        scores["core_technology_differentiation"] = self._score_core_technology_differentiation(
            all_docs, company_name
        )

        # Criterion 2: Patent Portfolio (5 points max)
        scores["patent_portfolio"] = self._score_patent_portfolio(
            doc_categories["patents"]
        )

        # Criterion 3: Research / Technical Validation (4 points max)
        scores["research_validation"] = self._score_research_validation(
            doc_categories["research_papers"],
            doc_categories["whitepapers"],
            doc_categories["validation_docs"]
        )

        # Criterion 4: Product Linkage / Commercialization Relevance (3 points max)
        scores["product_linkage"] = self._score_product_linkage(
            doc_categories["product_docs"],
            doc_categories["patents"],
            doc_categories["research_papers"],
            company_name
        )

        # Criterion 5: Scalability / Applicability Breadth (2 points max)
        scores["scalability"] = self._score_scalability(all_docs, company_name)

        return scores

    def _score_core_technology_differentiation(self, docs: list, company_name: str) -> int:
        """
        Score core technology differentiation (0-6 points).
        
        6: Clearly differentiated proprietary technology, algorithm, process, or method
        3: Meaningful improvement over existing solutions
        1: Mostly generic AI/software or weak differentiation
        0: Differentiation unclear
        """
        if not docs:
            return 0

        differentiation_signals = 0
        content = " ".join([getattr(doc, 'content', "") or "" for doc in docs[:5]])
        content_lower = content.lower()

        # Strong differentiation signals
        strong_signals = [
            "proprietary", "novel", "unique", "patented", "breakthrough",
            "first", "invented", "proprietary method", "proprietary algorithm"
        ]
        for signal in strong_signals:
            if signal in content_lower:
                differentiation_signals += 2
                break

        # Medium differentiation signals (meaningful improvement)
        if differentiation_signals == 0:
            medium_signals = ["improved", "optimized", "enhanced", "advanced", "innovative"]
            for signal in medium_signals:
                if signal in content_lower:
                    differentiation_signals += 1
                    break

        # Additional signals of technical depth
        if any(x in content_lower for x in ["algorithm", "method", "process", "framework", "architecture"]):
            differentiation_signals += 0.5

        # Award points based on accumulated signals
        if differentiation_signals >= 2.5:
            return 6
        elif differentiation_signals >= 1.5:
            return 3
        elif differentiation_signals >= 0.5:
            return 1
        else:
            return 0

    def _score_patent_portfolio(self, patent_docs: list) -> int:
        """
        Score patent portfolio (0-5 points).
        
        5: 3+ registered patents and/or PCT international patent applications
        3: 1-2 patents/applications with product relevance
        1: Patent/application exists but weak relevance or defensibility
        0: No patent evidence found
        """
        if not patent_docs:
            return 0

        patent_count = len(patent_docs)
        
        # Look for PCT or international application indicators
        pct_count = 0
        content = " ".join([getattr(doc, 'content', "") or "" for doc in patent_docs])
        content_lower = content.lower()

        if any(x in content_lower for x in ["pct", "international", "world intellectual property"]):
            pct_count = 1

        total_strength = patent_count + pct_count

        if total_strength >= 3:
            return 5
        elif total_strength >= 1:
            return 3
        else:
            return 1

    def _score_research_validation(
        self,
        paper_docs: list,
        whitepaper_docs: list,
        validation_docs: list
    ) -> int:
        """
        Score research and technical validation (0-4 points).
        
        4: SCI/SCIE papers, major conference papers, or strong third-party technical validation
        2: Internal whitepapers, field trials, or internal experimental validation
        0: No meaningful technical validation found
        """
        total_docs = len(paper_docs) + len(whitepaper_docs) + len(validation_docs)
        
        if not total_docs:
            return 0

        # Check for peer-reviewed or major venue indicators
        all_content = " ".join([
            getattr(doc, 'content', "") or ""
            for doc in paper_docs + whitepaper_docs + validation_docs
        ])
        content_lower = all_content.lower()

        # Strong validation: peer-reviewed or high-impact venue
        strong_validation = any(x in content_lower for x in [
            "peer reviewed", "peer-reviewed", "published", "ieee", "acm", "springer",
            "journal", "conference", "sci", "scie", "impact factor", "indexed"
        ])

        # Medium validation: field tests or internal validation
        medium_validation = any(x in content_lower for x in [
            "field trial", "experiment", "validated", "verified", "tested", "benchmark", "result"
        ])

        if strong_validation and len(paper_docs) > 0:
            return 4
        elif medium_validation or len(whitepaper_docs) > 0 or len(validation_docs) > 0:
            return 2
        elif len(paper_docs) > 0:
            return 2
        else:
            return 0

    def _score_product_linkage(
        self,
        product_docs: list,
        patent_docs: list,
        paper_docs: list,
        company_name: str
    ) -> int:
        """
        Score product linkage of patents/papers (0-3 points).
        
        3: Patents/papers are directly tied to core product or main commercial offering
        1: Partial or indirect linkage to product
        0: Linkage unclear or technology is research-only
        """
        linkage_signals = 0

        # Signal 1: Existence of product documentation
        if product_docs:
            linkage_signals += 1

        # Signal 2: Evidence of commercialization language
        all_content = " ".join([
            getattr(doc, 'content', "") or ""
            for doc in product_docs + patent_docs + paper_docs
        ])
        content_lower = all_content.lower()

        product_signals = [
            "product", "application", "feature", "offering", "commerciali",
            "market", "customer", "service", "platform"
        ]
        for signal in product_signals:
            if signal in content_lower:
                linkage_signals += 1
                break

        # Signal 3: Company-specific linkage (mentioned in product/patent context)
        snippets = self._company_snippets(all_content, company_name, window=300)
        if snippets:
            linkage_signals += 1

        if linkage_signals >= 2:
            return 3
        elif linkage_signals >= 1:
            return 1
        else:
            return 0

    def _score_scalability(self, docs: list, company_name: str) -> int:
        """
        Score scalability and applicability breadth (0-2 points).
        
        2: Applicable across multiple crops, environments, regions, or as platform technology
        1: Limited expansion potential or single-crop/single-condition focus
        0: Narrow single-use technology
        """
        all_content = " ".join([getattr(doc, 'content', "") or "" for doc in docs])
        content_lower = all_content.lower()

        scalability_signals = 0

        # Signals of broad applicability
        broad_signals = [
            "platform", "multi-crop", "multiple crops", "various crops", "different crops",
            "multi-region", "multiple regions", "global", "scalable", "versatile",
            "agnostic", "livestock", "animals", "across", "ecosystem"
        ]

        for signal in broad_signals:
            if signal in content_lower:
                scalability_signals += 1.5
                break

        # Additional signals: integration/extensibility
        if any(x in content_lower for x in ["integration", "api", "sdk", "framework", "plugin"]):
            scalability_signals += 0.5

        # Score based on accumulated signals
        if scalability_signals >= 1.5:
            return 2
        elif scalability_signals >= 0.5:
            return 1
        elif any(x in content_lower for x in ["specific", "particular", "limited", "single"]):
            return 1
        else:
            return 0

    def _build_criterion_summary(self, scores: dict) -> str:
        """Build human-readable summary string of criterion scores."""
        summary_parts = []
        criterion_order = [
            "core_technology_differentiation",
            "patent_portfolio",
            "research_validation",
            "product_linkage",
            "scalability"
        ]
        
        for criterion in criterion_order:
            if criterion in scores:
                readable = criterion.replace("_", " ").title()
                score = scores[criterion]
                summary_parts.append(f"{readable}: {score}")
        
        return " | ".join(summary_parts)

    def _add_missing_information_notes(self, result: TechnologyAnalysisResult, scores: dict) -> None:
        """Add missing information notes based on low or zero scores."""
        if scores.get("patent_portfolio", 0) == 0:
            result.missing_information.append(
                "No patent or PCT application evidence found in retrieved documents"
            )

        if scores.get("research_validation", 0) == 0:
            result.missing_information.append(
                "No research papers or technical validation documentation found"
            )

        if scores.get("product_linkage", 0) == 0:
            result.missing_information.append(
                "Product linkage of technology unclear; product-specific documentation not retrieved"
            )

        if scores.get("scalability", 0) == 0:
            result.missing_information.append(
                "Scalability and applicability breadth not evident in available documents"
            )

        if scores.get("core_technology_differentiation", 0) <= 1:
            result.missing_information.append(
                "Differentiation from existing solutions is unclear; core technology may require clarification"
            )

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        """Clamp a score to the configured range [minimum, maximum]."""
        return max(minimum, min(maximum, value))
