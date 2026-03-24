"""Impact Evaluation Agent - Evaluates environmental and agricultural impact using FAISS + OpenAI."""

import json
import os
from typing import Optional

from openai import OpenAI
from models import ImpactAnalysisResult, EvidenceItem
from rag import Retriever
from .base_agent import BaseAgent


RUBRIC = """
## E. 임팩트 & 지속가능성 평가 기준 (총 15점)

### 1. SDG 2 기여도 (만점 6점)
- 6점: 식량 생산성 20%+ 향상 또는 식량 손실 감축이 정량화됨
- 3점: 간접 기여 (노동력 해소, 공급망 효율화, 생태계 지원 등)
- 0점: SDG 2와 무관

### 2. 탄소·물 감축 (만점 5점)
- 5점: 탄소 또는 물 사용 15%+ 감축이 검증된 수치로 제시됨
- 2점: 감축 목표만 있고 검증 수치 없음
- 0점: 탄소·물 감축 내용 없음

### 3. ESG 투자자 어필 (만점 4점)
- 4점: 임팩트 VC 또는 ESG 펀드 LP 유치 확인됨
- 2점: 지속가능성 관심 표명 수준
- 0점: ESG 투자자 없음
"""


class ImpactEvaluationAgent(BaseAgent):
    """Agent responsible for evaluating environmental and agricultural impact."""

    def __init__(self):
        super().__init__(
            name="ImpactEvaluationAgent",
            description="Evaluates environmental, agricultural, and sustainability impact",
        )
        self._openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def execute(
        self,
        startup_name: str,
        retriever: Optional[Retriever] = None,
    ) -> ImpactAnalysisResult:
        self.start_execution()
        try:
            self.log_info(f"Evaluating impact for {startup_name}")

            # ── 1. FAISS 검색: 항목별 쿼리 ──────────────────────────────
            docs_sdg2, docs_carbon, docs_esg = [], [], []
            if retriever:
                docs_sdg2 = self.retrieve_documents(
                    retriever,
                    f"{startup_name} SDG 2 식량 생산성 yield food security 수확량 기여",
                    top_k=3,
                )
                docs_carbon = self.retrieve_documents(
                    retriever,
                    f"{startup_name} 탄소 물 감축 carbon water reduction GHG emission 메탄",
                    top_k=3,
                )
                docs_esg = self.retrieve_documents(
                    retriever,
                    f"{startup_name} ESG 임팩트 VC 투자자 impact fund investor",
                    top_k=3,
                )

            # ── 2. 문서 컨텍스트 구성 ────────────────────────────────────
            def fmt_docs(docs, label):
                if not docs:
                    return f"[{label}] 관련 문서 없음\n"
                parts = [f"[{label}]"]
                for d in docs:
                    parts.append(f"  - (score={d.relevance_score:.2f}) {d.content[:400]}")
                return "\n".join(parts)

            context = "\n\n".join([
                fmt_docs(docs_sdg2, "SDG2 관련"),
                fmt_docs(docs_carbon, "탄소·물 감축 관련"),
                fmt_docs(docs_esg, "ESG 투자자 관련"),
            ])

            # ── 3. OpenAI 호출 ───────────────────────────────────────────
            prompt = f"""당신은 AgTech 임팩트 투자 분석가입니다.
아래 검색된 문서를 바탕으로 **{startup_name}** 기업의 임팩트 & 지속가능성을 평가하세요.

{RUBRIC}

## 검색된 문서
{context}

## 출력 형식 (JSON만 반환, 다른 텍스트 없이)
{{
  "sdg2_score": <0 or 3 or 6>,
  "sdg2_reason": "<한 문장 근거>",
  "carbon_water_score": <0 or 2 or 5>,
  "carbon_water_reason": "<한 문장 근거>",
  "esg_score": <0 or 2 or 4>,
  "esg_reason": "<한 문장 근거>",
  "yield_improvement_claimed": "<수치 있으면 기재, 없으면 null>",
  "carbon_reduction_claimed": "<수치 있으면 기재, 없으면 null>",
  "water_saving_claimed": "<수치 있으면 기재, 없으면 null>",
  "sustainability_focus": ["<핵심 지속가능성 분야 1~3개>"],
  "efficiency_improvements": ["<효율 개선 사항 1~3개>"],
  "missing_information": ["<평가에 필요했으나 없는 정보>"]
}}"""

            response = self._openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"},
            )
            raw = json.loads(response.choices[0].message.content)

            # ── 4. 결과 조립 ──────────────────────────────────────────────
            sdg2 = int(raw.get("sdg2_score", 0))
            carbon = int(raw.get("carbon_water_score", 0))
            esg = int(raw.get("esg_score", 0))

            result = ImpactAnalysisResult(
                sdg2_score=sdg2,
                carbon_water_score=carbon,
                esg_score=esg,
                total_impact_score=sdg2 + carbon + esg,
                sdg2_reason=raw.get("sdg2_reason", ""),
                carbon_water_reason=raw.get("carbon_water_reason", ""),
                esg_reason=raw.get("esg_reason", ""),
                agricultural_impact=round(sdg2 / 6, 4),
                environmental_impact=round(carbon / 5, 4),
                yield_improvement_claimed=raw.get("yield_improvement_claimed"),
                carbon_reduction_claimed=raw.get("carbon_reduction_claimed"),
                water_saving_claimed=raw.get("water_saving_claimed"),
                sustainability_focus=raw.get("sustainability_focus", []),
                efficiency_improvements=raw.get("efficiency_improvements", []),
                missing_information=raw.get("missing_information", []),
            )

            # ── 5. 증거 추가 ──────────────────────────────────────────────
            for label, docs in [("SDG2", docs_sdg2), ("탄소물", docs_carbon), ("ESG", docs_esg)]:
                for doc in docs[:2]:
                    result.evidence.append(EvidenceItem(
                        claim=f"[{label}] {doc.content[:100]}",
                        source_document=doc.source,
                        evidence_type="impact_claim",
                        confidence=doc.relevance_score,
                        supporting_details=doc.content[:300],
                    ))

            result.summary = (
                f"{startup_name} 임팩트 총점: {result.total_impact_score}/15 "
                f"(SDG2={sdg2}/6, 탄소물={carbon}/5, ESG={esg}/4)"
            )
            self.log_info(result.summary)
            return result

        finally:
            self.end_execution()


if __name__ == "__main__":
    import sys
    import logging

    os.chdir(os.path.join(os.path.dirname(__file__), ".."))

    from dotenv import load_dotenv
    load_dotenv()

    from app.main import initialize_retriever

    startup_name = sys.argv[1] if len(sys.argv) > 1 else "Regrow"

    retriever = initialize_retriever(logging.getLogger("main"))

    agent = ImpactEvaluationAgent()
    result = agent.execute(startup_name, retriever=retriever)

    print(f"\n{'='*60}")
    print(result.summary)
    print(f"{'='*60}")
    print(f"  SDG 2     : {result.sdg2_score}/6  → {result.sdg2_reason}")
    print(f"  탄소·물    : {result.carbon_water_score}/5  → {result.carbon_water_reason}")
    print(f"  ESG 투자자 : {result.esg_score}/4  → {result.esg_reason}")
    print(f"\n  agricultural_impact : {result.agricultural_impact:.2f}")
    print(f"  environmental_impact: {result.environmental_impact:.2f}")
    if result.yield_improvement_claimed:
        print(f"\n  수확량 향상 : {result.yield_improvement_claimed}")
    if result.carbon_reduction_claimed:
        print(f"  탄소 감축  : {result.carbon_reduction_claimed}")
    if result.water_saving_claimed:
        print(f"  물 절감    : {result.water_saving_claimed}")
    if result.missing_information:
        print(f"\n  [미확인 정보] {result.missing_information}")
