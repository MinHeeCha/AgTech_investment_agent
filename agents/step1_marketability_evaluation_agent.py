"""Marketability Evaluation Agent - Analyzes market potential."""

import re
from typing import Optional
from models import MarketabilityAnalysisResult, EvidenceItem
from rag import Retriever
from .base_agent import BaseAgent


class MarketabilityEvaluationAgent(BaseAgent):
    """Agent responsible for evaluating market potential and business model."""

    def __init__(self):
        super().__init__(
            name="MarketabilityEvaluationAgent",
            description="Evaluates target market, customer pain points, and commercial feasibility",
        )

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        """Clamp a score to the configured range."""
        return max(minimum, min(maximum, value))

    @staticmethod
    def _extract_market_size(text: str) -> Optional[str]:
        """Extract a market size expression like '$50B' or '$1.2 trillion'."""
        match = re.search(
            r"(\$ ?\d+(?:\.\d+)?\s?(?:[KMBT]|million|billion|trillion)\+?)",
            text,
            flags=re.IGNORECASE,
        )
        return match.group(1) if match else None

    @staticmethod
    def _extract_sam_usd_amount(text: str) -> Optional[float]:
        """
        Extract SAM-like USD amount and return as raw USD value.

        Supports expressions such as:
        - $1B, $500M, USD 1.2 billion, 750 million USD
        """
        text_l = (text or "").lower()
        patterns = [
            r"(?:\$|usd\s*)\s*(\d+(?:\.\d+)?)\s*(k|m|b|t|million|billion|trillion)",
            r"(\d+(?:\.\d+)?)\s*(k|m|b|t|million|billion|trillion)\s*(?:usd|\$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_l, flags=re.IGNORECASE)
            if not match:
                continue
            value = float(match.group(1))
            unit = match.group(2).lower()
            multiplier = {
                "k": 1_000,
                "m": 1_000_000,
                "million": 1_000_000,
                "b": 1_000_000_000,
                "billion": 1_000_000_000,
                "t": 1_000_000_000_000,
                "trillion": 1_000_000_000_000,
            }.get(unit)
            if multiplier is not None:
                return value * multiplier
        return None

    @staticmethod
    def _extract_cagr_percent(text: str) -> Optional[float]:
        """
        Extract CAGR percentage from text.

        Supports patterns such as:
        - CAGR 18%
        - 18% CAGR
        - cagr: 22.5 %
        """
        text_l = (text or "").lower()
        patterns = [
            r"cagr[^0-9]{0,10}(\d+(?:\.\d+)?)\s*%",
            r"(\d+(?:\.\d+)?)\s*%\s*cagr",
        ]
        for pattern in patterns:
            match = re.search(pattern, text_l, flags=re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None

    @staticmethod
    def _sam_score_from_usd(sam_usd: Optional[float]) -> int:
        """SAM rubric: >=$1B=6, $500M~$1B=4, <$500M=1."""
        if sam_usd is None:
            return 1
        if sam_usd >= 1_000_000_000:
            return 6
        if sam_usd >= 500_000_000:
            return 4
        return 1

    @staticmethod
    def _cagr_score(cagr_percent: Optional[float]) -> int:
        """CAGR rubric: >=20%=5, 10~20%=3, <10%=1."""
        if cagr_percent is None:
            return 1
        if cagr_percent >= 20.0:
            return 5
        if cagr_percent >= 10.0:
            return 3
        return 1

    @staticmethod
    def _company_tokens(company_name: str) -> list[str]:
        """Build normalized company-name tokens for mention matching."""
        tokens = re.split(r"[^a-z0-9]+", (company_name or "").lower())
        return [token for token in tokens if len(token) >= 3]

    @classmethod
    def _company_snippets(cls, text: str, company_name: str, window: int = 220) -> list[str]:
        """
        Return short snippets around company mentions.

        This reduces cross-company contamination when one chunk contains many companies.
        """
        if not text or not company_name:
            return []

        patterns = [re.escape(company_name.strip())]
        patterns.extend(rf"\b{re.escape(token)}\b" for token in cls._company_tokens(company_name))

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
        return snippets

    @classmethod
    def _contains_company_mention(cls, text: str, company_name: str) -> bool:
        """Check whether the text explicitly mentions the target company."""
        return bool(cls._company_snippets(text, company_name, window=120))

    def execute(self, company_name: str,
               retriever: Optional[Retriever] = None) -> MarketabilityAnalysisResult:
        """
        Evaluate startup marketability.

        Args:
            company_name: Company name to analyze
            retriever: Optional Retriever for market information

        Returns:
            MarketabilityAnalysisResult
        """
        self.start_execution()

        try:
            self.log_info(f"Evaluating marketability for {company_name}")

            result = MarketabilityAnalysisResult(
                target_market_size=None,
                market_growth_potential=1,
                business_model="SaaS subscription and usage-based pricing",
                commercial_feasibility_score=2,
            )

            # Identify customer pain points
            result.customer_pain_points = [
                "Crop monitoring and early disease detection",
                "Optimization of irrigation and water usage",
                "Labor shortage for crop management",
                "Inconsistent yield prediction",
            ]

            # Identify adoption barriers
            result.adoption_barriers = [
                "Farmer technology adoption curve",
                "Integration with existing farm management systems",
                "Regulatory compliance in different regions",
            ]

            # Retrieve market information if retriever available
            if retriever:
                raw_market_docs = self.retrieve_documents(
                    retriever,
                    f"{company_name} market customers business model revenue agriculture",
                    top_k=5
                )
                market_docs = [
                    doc for doc in raw_market_docs
                    if self._contains_company_mention(doc.content or "", company_name)
                ]
                if not market_docs:
                    market_docs = raw_market_docs
                    result.missing_information.append(
                        "No company-specific market chunks found; fallback used broader retrieved chunks"
                    )

                # Create evidence from market documents
                for doc in market_docs[:3]:
                    evidence = EvidenceItem(
                        claim=f"Market information from {doc.source}",
                        source_document=doc.source,
                        evidence_type="market_data",
                        confidence=doc.relevance_score,
                        supporting_details=doc.content[:200] if doc.content else None
                    )
                    result.evidence.append(evidence)

                sam_candidates = []
                cagr_candidates = []

                # Infer market size from retrieved content
                for doc in market_docs:
                    content = doc.content or ""
                    snippets = self._company_snippets(content, company_name)
                    scoped_texts = snippets if snippets else [content]

                    for scoped_text in scoped_texts:
                        extracted_size = self._extract_market_size(scoped_text)
                        if extracted_size:
                            result.target_market_size = (
                                f"Approx. {extracted_size} referenced near {company_name} mentions"
                            )

                        sam_value = self._extract_sam_usd_amount(scoped_text)
                        if sam_value is not None:
                            sam_candidates.append(sam_value)

                        cagr_value = self._extract_cagr_percent(scoped_text)
                        if cagr_value is not None:
                            cagr_candidates.append(cagr_value)

                best_sam_usd = max(sam_candidates) if sam_candidates else None
                best_cagr = max(cagr_candidates) if cagr_candidates else None

                sam_score = self._sam_score_from_usd(best_sam_usd)
                cagr_score = self._cagr_score(best_cagr)

                # Map rubric scores to model fields (0~11)
                result.market_growth_potential = cagr_score                     #  1, 3, 5
                result.commercial_feasibility_score = sam_score + cagr_score    #  2 ~ 11

                # Infer business model hints from retrieved content
                business_model_signals = []
                for doc in market_docs:
                    content = doc.content or ""
                    snippets = self._company_snippets(content, company_name)
                    scoped_texts = snippets if snippets else [content]

                    for scoped_text in scoped_texts:
                        snippet = scoped_text.lower()
                        if "subscription" in snippet or "saas" in snippet:
                            business_model_signals.append("SaaS subscription")
                        if "license" in snippet or "licensing" in snippet:
                            business_model_signals.append("Licensing")
                        if "transaction" in snippet or "marketplace" in snippet:
                            business_model_signals.append("Transaction / marketplace")
                        if "hardware" in snippet or "device" in snippet:
                            business_model_signals.append("Hardware + service")

                if business_model_signals:
                    unique_models = list(dict.fromkeys(business_model_signals))
                    result.business_model = ", ".join(unique_models[:3])

                if best_sam_usd is None:
                    result.missing_information.append("SAM value not found in retrieved documents; SAM set to 1 point")
                if best_cagr is None:
                    result.missing_information.append("CAGR value not found in retrieved documents; CAGR set to 1 point")
            else:
                result.missing_information.append("Retriever not provided; market scoring fallback used")

            # Add missing information
            if not result.target_market_size:
                result.missing_information.append("TAM sizing information not found")

            result.summary = f"Market Growth Potential: {result.market_growth_potential}/5. " \
                           f"Commercial Feasibility: {result.commercial_feasibility_score}/11. " \
                           f"Business Model: {result.business_model}. " \
                           f"(SAM/CAGR rubric applied)"

            self.log_info(f"Marketability analysis complete for {company_name}")

            return result

        finally:
            self.end_execution()
