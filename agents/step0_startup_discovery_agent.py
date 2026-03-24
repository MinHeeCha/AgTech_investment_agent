"""Startup Discovery Agent - Retrieves the list of candidate startups from the vector DB."""

import json
import os

from openai import OpenAI
from rag import Retriever
from .base_agent import BaseAgent


class StartupDiscoveryAgent(BaseAgent):
    """Searches the vector DB for AgTech startup names and returns them as a list."""

    def __init__(self):
        super().__init__(
            name="StartupDiscoveryAgent",
            description="Retrieves AgTech startup candidates from the vector DB",
        )
        self._openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def execute(self, retriever: Retriever) -> list[str]:
        """
        Query the vector DB for company listing chunks and extract startup names.

        Args:
            retriever: Retriever instance backed by the FAISS index

        Returns:
            List of startup name strings
        """
        self.start_execution()
        try:
            # ── 1. 기업 목록이 담긴 청크 검색 ──────────────────────────
            docs = self.retrieve_documents(
                retriever,
                "AgTech 기업 목록 회사 리스트 Series A Series B",
                top_k=5,
            )

            if not docs:
                self.log_warning("No company listing chunks found in vector DB")
                return []

            context = "\n\n".join(
                f"[{i+1}] {doc.content[:800]}" for i, doc in enumerate(docs)
            )

            # ── 2. LLM으로 기업명만 추출 ─────────────────────────────────
            prompt = f"""아래 문서에서 AgTech 스타트업 회사 이름만 추출해서 JSON 배열로 반환하세요.
회사명 외에 국가, 도시, 설명 등은 포함하지 마세요.
중복은 제거하세요.

## 문서
{context}

## 출력 형식 (JSON 배열만, 다른 텍스트 없이)
["회사명1", "회사명2", ...]"""

            response = self._openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"},
            )

            raw = json.loads(response.choices[0].message.content)

            # JSON object로 반환될 경우 배열 값 추출
            if isinstance(raw, dict):
                names = next(iter(raw.values()))
            else:
                names = raw

            self.log_info(f"Discovered {len(names)} startups")
            return names

        finally:
            self.end_execution()


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))

    from dotenv import load_dotenv
    load_dotenv()

    from app.main import initialize_retriever
    import logging

    retriever = initialize_retriever(logging.getLogger("main"))
    agent = StartupDiscoveryAgent()
    names = agent.execute(retriever)

    print(f"\n발견된 기업 ({len(names)}개):")
    for i, name in enumerate(names, 1):
        print(f"  {i:2d}. {name}")
