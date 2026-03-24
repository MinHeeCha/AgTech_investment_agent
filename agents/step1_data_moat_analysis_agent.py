"""Data Moat Analysis Agent - AgTech Investment Rubric C항목 기반 데이터 해자 평가."""

import os
from typing import Optional
from openai import OpenAI
from models import DataMoatAnalysisResult, EvidenceItem
from rag import Retriever
from .base_agent import BaseAgent


# ── 회사 유형 분류 ────────────────────────────────────────────────────────────
# 데이터 해자가 아닌 IP 해자로 평가해야 하는 바이오/제품형 회사 목록
# 새로운 회사가 추가될 경우 여기에 등록
IP_MOAT_COMPANIES = {
    "micropep", "micropep technologies",
    "nitricity",
    "elicit plant",
    "ch4 global",
    "vive crop", "vive crop protection",
    "windfall bio",
    "biomedit",
    "genomines",
}

# ── 루브릭 상수 (이미지 기준 C. 데이터 해자 분석, 총 20점) ───────────────────
class DatasetSizeScore:
    """독자 데이터셋 규모 (만점 8점)"""
    LARGE  = 8   # 100만+ 에이커 또는 10만+ 농가 데이터
    MEDIUM = 5   # 1만+ 에이커 또는 1만+ 농가 데이터
    SMALL  = 1   # 미공개 / 미확보

class ExclusiveContractScore:
    """데이터 독점 계약 (만점 7점)"""
    EXCLUSIVE     = 7   # 농가·파트너와 독점 데이터 공유 계약
    NON_EXCLUSIVE = 3   # 비독점 파트너십
    NONE          = 0   # 계약 없음

class NetworkEffectScore:
    """네트워크 효과 (만점 5점)"""
    AUTO   = 5   # 사용자 증가 → 모델 자동 개선 구조 (데이터 플라이휠)
    MANUAL = 2   # 수동 개선
    NONE   = 0   # 해당 없음


class DataMoatAnalysisAgent(BaseAgent):
    """
    AgTech Investment Rubric — C. 데이터 해자 분석 (20점)

    항목별 채점:
      - 독자 데이터셋 규모  : 최대  8점
      - 데이터 독점 계약    : 최대  7점
      - 네트워크 효과       : 최대  5점
    총점: 20점

    바이오/제품형(IP_MOAT_COMPANIES)은 데이터 해자 대신 IP 해자로 자동 전환.
    """

    def __init__(self):
        super().__init__(
            name="DataMoatAnalysisAgent",
            description=(
                "AgTech Rubric C항목: 독자 데이터셋 규모(8점), "
                "데이터 독점 계약(7점), 네트워크 효과(5점) — 총 20점 채점"
            ),
        )
        self._openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # ── 퍼블릭 진입점 ──────────────────────────────────────────────────────────
    def execute(
        self,
        startup_name: str,
        retriever: Optional[Retriever] = None,
    ) -> DataMoatAnalysisResult:
        """
        데이터 해자 분석 실행.

        Args:
            startup_name: 평가 대상 스타트업 이름
            retriever   : RAG 검색기 (없으면 LLM 추론만 사용)

        Returns:
            DataMoatAnalysisResult  (total_score 포함)
        """
        self.start_execution()

        try:
            self.log_info(f"[DataMoat] 시작 — {startup_name}")

            # ── Step 1. 회사 유형 판별 ─────────────────────────────────────
            is_ip_moat_type = startup_name.lower() in IP_MOAT_COMPANIES

            if is_ip_moat_type:
                result = self._evaluate_ip_moat(startup_name, retriever)
            else:
                result = self._evaluate_data_moat(startup_name, retriever)

            # ── Step 2. 누락 정보 플래그 ───────────────────────────────────
            self._flag_missing_information(result)

            # ── Step 3. 최종 요약 문장 생성 ────────────────────────────────
            result.summary = self._build_summary(startup_name, result, is_ip_moat_type)

            self.log_info(
                f"[DataMoat] 완료 — {startup_name} | "
                f"총점: {result.total_score}/20 | 유형: "
                f"{'IP 해자' if is_ip_moat_type else '데이터 해자'}"
            )
            return result

        finally:
            self.end_execution()

    # ── 데이터 해자 평가 (플랫폼형·하드웨어+데이터형) ─────────────────────────
    def _evaluate_data_moat(
        self,
        startup_name: str,
        retriever: Optional[Retriever],
    ) -> DataMoatAnalysisResult:
        """
        C항목 세 가지 기준을 LLM + RAG로 채점.
        """
        # RAG 검색 — 에이커·농가 수·파트너십·플라이휠 키워드로 검색
        rag_context = ""
        if retriever:
            queries = [
                f"{startup_name} acres hectares farmers data coverage",
                f"{startup_name} exclusive data partnership agreement",
                f"{startup_name} data flywheel network effect model improvement",
            ]
            docs = []
            for q in queries:
                docs.extend(
                    self.retrieve_documents(retriever, q, top_k=3)
                )

            # 중복 제거 (source 기준)
            seen = set()
            unique_docs = []
            for d in docs:
                if d.source not in seen:
                    seen.add(d.source)
                    unique_docs.append(d)

            rag_context = "\n\n".join(
                f"[출처: {d.source}]\n{d.content[:400]}"
                for d in unique_docs[:6]
            )

        # LLM 채점 프롬프트
        prompt = self._build_data_moat_prompt(startup_name, rag_context)
        llm_response = self._openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        parsed = self._parse_llm_response(llm_response)

        # ── 항목별 점수 매핑 ────────────────────────────────────────────────
        dataset_score    = self._score_dataset_size(parsed.get("dataset_size_level", "small"))
        contract_score   = self._score_exclusive_contract(parsed.get("contract_level", "none"))
        network_score    = self._score_network_effect(parsed.get("network_effect_level", "none"))
        total_score      = dataset_score + contract_score + network_score

        # ── 결과 객체 구성 ───────────────────────────────────────────────────
        result = DataMoatAnalysisResult(
            moat_type                  = "data",
            has_proprietary_datasets   = dataset_score > 1,
            dataset_size_level         = parsed.get("dataset_size_level", "small"),
            dataset_size_description   = parsed.get("dataset_size_description", ""),
            contract_level             = parsed.get("contract_level", "none"),
            contract_description       = parsed.get("contract_description", ""),
            network_effect_level       = parsed.get("network_effect_level", "none"),
            network_effect_description = parsed.get("network_effect_description", ""),
            # 루브릭 점수
            dataset_size_score         = dataset_score,    # /8
            exclusive_contract_score   = contract_score,   # /7
            network_effect_score       = network_score,    # /5
            total_score                = total_score,      # /20
            # 기존 필드 호환성 유지
            dataset_defensibility_score = round(total_score / 20, 2),
            data_flywheel_potential     = round(network_score / 5, 2),
            moat_strength_score         = round(total_score / 20, 2),
            data_assets_description     = parsed.get("dataset_size_description", ""),
            sensing_pipeline_uniqueness = parsed.get("contract_description", ""),
        )

        # RAG 근거 evidence 추가
        if retriever and unique_docs:
            for doc in unique_docs[:4]:
                result.evidence.append(
                    EvidenceItem(
                        claim               = f"{startup_name} 데이터 자산 근거",
                        source_document     = doc.source,
                        evidence_type       = "data_asset",
                        confidence          = doc.relevance_score,
                        supporting_details  = doc.content[:300],
                    )
                )

        return result

    # ── IP 해자 평가 (바이오·제품형 폴백) ─────────────────────────────────────
    def _evaluate_ip_moat(
        self,
        startup_name: str,
        retriever: Optional[Retriever],
    ) -> DataMoatAnalysisResult:
        """
        바이오/제품형 회사는 데이터 해자 대신 IP 해자(특허·독점계약)로 대체 평가.
        데이터 해자 점수(0점)로 기록하고, ip_moat_note에 실제 IP 강점을 기술.
        """
        rag_context = ""
        if retriever:
            docs = self.retrieve_documents(
                retriever,
                f"{startup_name} patent license exclusive agreement field trial",
                top_k=5,
            )
            rag_context = "\n\n".join(
                f"[출처: {d.source}]\n{d.content[:400]}"
                for d in docs[:4]
            )

        prompt = self._build_ip_moat_prompt(startup_name, rag_context)
        llm_response = self._openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        parsed = self._parse_llm_response(llm_response)

        # 데이터 해자 점수는 0으로 고정, IP 강점 별도 필드에 기록
        result = DataMoatAnalysisResult(
            moat_type                  = "ip",
            has_proprietary_datasets   = False,
            dataset_size_level         = "not_applicable",
            contract_level             = "not_applicable",
            network_effect_level       = "not_applicable",
            dataset_size_score         = 0,
            exclusive_contract_score   = 0,
            network_effect_score       = 0,
            total_score                = 0,   # 데이터 해자 점수는 0
            dataset_defensibility_score = 0.0,
            data_flywheel_potential     = 0.0,
            moat_strength_score         = 0.0,
            # IP 해자 관련 필드
            ip_moat_note               = parsed.get("ip_moat_note", ""),
            patent_count               = parsed.get("patent_count", "미확인"),
            field_trial_description    = parsed.get("field_trial_description", ""),
            big_corp_partnership       = parsed.get("big_corp_partnership", ""),
            data_assets_description    = "해당 없음 — IP 해자 유형 기업",
            sensing_pipeline_uniqueness= parsed.get("ip_moat_note", ""),
        )

        return result

    # ── 점수 매핑 함수 ─────────────────────────────────────────────────────────
    @staticmethod
    def _score_dataset_size(level: str) -> int:
        """
        독자 데이터셋 규모 채점 (8점 만점)
        level: "large" | "medium" | "small"
        """
        return {
            "large" : DatasetSizeScore.LARGE,   # 100만+ 에이커 / 10만+ 농가
            "medium": DatasetSizeScore.MEDIUM,  # 1만+ 에이커 / 1만+ 농가
            "small" : DatasetSizeScore.SMALL,   # 미공개 / 미확보
        }.get(level, DatasetSizeScore.SMALL)

    @staticmethod
    def _score_exclusive_contract(level: str) -> int:
        """
        데이터 독점 계약 채점 (7점 만점)
        level: "exclusive" | "non_exclusive" | "none"
        """
        return {
            "exclusive"    : ExclusiveContractScore.EXCLUSIVE,
            "non_exclusive": ExclusiveContractScore.NON_EXCLUSIVE,
            "none"         : ExclusiveContractScore.NONE,
        }.get(level, ExclusiveContractScore.NONE)

    @staticmethod
    def _score_network_effect(level: str) -> int:
        """
        네트워크 효과 채점 (5점 만점)
        level: "auto" | "manual" | "none"
        """
        return {
            "auto"  : NetworkEffectScore.AUTO,
            "manual": NetworkEffectScore.MANUAL,
            "none"  : NetworkEffectScore.NONE,
        }.get(level, NetworkEffectScore.NONE)

    # ── 프롬프트 빌더 ─────────────────────────────────────────────────────────
    @staticmethod
    def _build_data_moat_prompt(startup_name: str, rag_context: str) -> str:
        return f"""
You are an AgTech investment analyst. Evaluate the data moat of the following startup.

## Startup
- Name: {startup_name}

## Retrieved Evidence
{rag_context if rag_context else "No RAG evidence available. Use general knowledge."}

## Scoring Rubric (AgTech Investment Rubric — Section C)

### 1. Dataset Size (dataset_size_level)
- "large"  → 1M+ acres OR 100K+ farmer data records → 8 points
- "medium" → 10K+ acres OR 10K+ farmer records      → 5 points
- "small"  → undisclosed / unconfirmed               → 1 point

### 2. Exclusive Data Contract (contract_level)
- "exclusive"     → exclusive data-sharing agreement with farms/partners → 7 points
- "non_exclusive" → non-exclusive partnership                            → 3 points
- "none"          → no known data agreement                              → 0 points

### 3. Network Effect (network_effect_level)
- "auto"   → more users → automatic model improvement (data flywheel) → 5 points
- "manual" → model improvement requires manual annotation/update       → 2 points
- "none"   → no network effect                                         → 0 points

## Output Format (JSON only, no markdown)
{{
  "dataset_size_level": "large|medium|small",
  "dataset_size_description": "구체적 수치 및 근거 (한국어, 1~2문장)",
  "contract_level": "exclusive|non_exclusive|none",
  "contract_description": "계약 현황 근거 (한국어, 1~2문장)",
  "network_effect_level": "auto|manual|none",
  "network_effect_description": "네트워크 효과 구조 설명 (한국어, 1~2문장)"
}}

Return ONLY valid JSON. No explanation outside JSON.
"""

    @staticmethod
    def _build_ip_moat_prompt(startup_name: str, rag_context: str) -> str:
        return f"""
You are an AgTech investment analyst. This company is classified as a biotech/physical-product type.
Data moat is NOT applicable. Evaluate IP moat instead.

## Startup
- Name: {startup_name}

## Retrieved Evidence
{rag_context if rag_context else "No RAG evidence available. Use general knowledge."}

## Output Format (JSON only, no markdown)
{{
  "ip_moat_note": "핵심 IP 해자 요약 (한국어, 2~3문장). 특허·독점기술·플랫폼 독점성 포함",
  "patent_count": "등록 특허 수 또는 '미확인'",
  "field_trial_description": "필드 트라이얼 규모 (나라 수, 에이커 등, 없으면 빈 문자열)",
  "big_corp_partnership": "대형 농화학·식품기업과 계약 현황 (없으면 빈 문자열)"
}}

Return ONLY valid JSON. No explanation outside JSON.
"""

    # ── LLM 응답 파싱 ─────────────────────────────────────────────────────────
    @staticmethod
    def _parse_llm_response(response) -> dict:
        """
        response_format=json_object 보장 환경에서의 파싱.
        실패 시 빈 dict 반환 (안전한 기본값으로 폴백).
        """
        import json
        try:
            raw = response.choices[0].message.content
            return json.loads(raw)
        except (json.JSONDecodeError, AttributeError, IndexError):
            return {}

    # ── 누락 정보 플래그 ──────────────────────────────────────────────────────
    @staticmethod
    def _flag_missing_information(result: DataMoatAnalysisResult) -> None:
        if result.moat_type == "data":
            if result.dataset_size_level == "small":
                result.missing_information.append(
                    "독자 데이터셋 규모 공개 자료 없음 — 추가 확인 필요"
                )
            if result.contract_level == "none":
                result.missing_information.append(
                    "데이터 독점 계약 확인 불가 — IR 자료 또는 공식 발표 확인 필요"
                )
            if result.network_effect_level == "none":
                result.missing_information.append(
                    "네트워크 효과 구조 미확인 — 기술 블로그 또는 논문 확인 필요"
                )

    # ── 요약 문장 생성 ────────────────────────────────────────────────────────
    @staticmethod
    def _build_summary(
        company_name: str,
        result: DataMoatAnalysisResult,
        is_ip_moat: bool,
    ) -> str:
        if is_ip_moat:
            return (
                f"[IP 해자 유형] {company_name}은 데이터 해자 대신 IP 해자로 평가됩니다. "
                f"{result.ip_moat_note or '상세 IP 정보 미확인.'}"
            )

        score_detail = (
            f"독자 데이터셋 {result.dataset_size_score}/8점 | "
            f"독점 계약 {result.exclusive_contract_score}/7점 | "
            f"네트워크 효과 {result.network_effect_score}/5점"
        )
        verdict = (
            "강한 데이터 해자" if result.total_score >= 15
            else "중간 데이터 해자" if result.total_score >= 8
            else "약한 데이터 해자"
        )
        return (
            f"[데이터 해자 평가] {company_name} — 총점 {result.total_score}/20점 ({verdict}). "
            f"{score_detail}. "
            f"{result.dataset_size_description or ''} "
            f"{result.contract_description or ''}"
        ).strip()

#######################################################################

if __name__ == "__main__":
    import json
    from types import SimpleNamespace

    # -----------------------------
    # 1) OpenAI 응답 목업
    # -----------------------------
    class DummyChatCompletions:
        def create(self, model, messages, temperature, response_format):
            prompt = messages[0]["content"]

            # IP 해자 분기용 더미 응답
            if "Evaluate IP moat instead" in prompt:
                payload = {
                    "ip_moat_note": "독점 기술과 현장 적용 노하우를 기반으로 한 IP 해자 가능성이 있습니다.",
                    "patent_count": "미확인",
                    "field_trial_description": "파일럿 운영 중",
                    "big_corp_partnership": ""
                }
            # 데이터 해자 분기용 더미 응답
            else:
                payload = {
                    "dataset_size_level": "medium",
                    "dataset_size_description": "공개 자료 기준 일정 규모의 운영 데이터 축적 가능성이 있습니다.",
                    "contract_level": "non_exclusive",
                    "contract_description": "비독점 파트너십 중심으로 보입니다.",
                    "network_effect_level": "manual",
                    "network_effect_description": "데이터가 쌓일수록 개선 여지는 있으나 자동 플라이휠은 제한적입니다."
                }

            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=json.dumps(payload, ensure_ascii=False))
                    )
                ]
            )

    class DummyOpenAI:
        def __init__(self):
            self.chat = SimpleNamespace(completions=DummyChatCompletions())

    # -----------------------------
    # 2) 테스트용 에이전트 서브클래스
    #    BaseAgent 의 외부 의존성을 최소화
    # -----------------------------
    class TestableDataMoatAnalysisAgent(DataMoatAnalysisAgent):
        def __init__(self):
            # super().__init__ 대신 최소 속성만 세팅
            self.name = "DataMoatAnalysisAgent"
            self.description = "test agent"
            self._openai = DummyOpenAI()

        def start_execution(self):
            print("[TEST] execution started")

        def end_execution(self):
            print("[TEST] execution ended")

        def log_info(self, message: str):
            print(message)

        def retrieve_documents(self, retriever, query, top_k=3):
            if retriever is None:
                return []
            return retriever.search(query, top_k=top_k)

    # -----------------------------
    # 3) 더미 retriever / document
    # -----------------------------
    class DummyDoc:
        def __init__(self, source, content, relevance_score=0.9):
            self.source = source
            self.content = content
            self.relevance_score = relevance_score

    class DummyRetriever:
        def search(self, query, top_k=3):
            return [
                DummyDoc(
                    source="dummy_source_1",
                    content=f"Mocked document for query: {query}",
                    relevance_score=0.91,
                ),
                DummyDoc(
                    source="dummy_source_2",
                    content=f"Additional mocked evidence for query: {query}",
                    relevance_score=0.87,
                ),
            ][:top_k]

    # -----------------------------
    # 4) 테스트용 startup 객체
    #    실제 StartupProfile이 pydantic/dataclass가 아니어도
    #    속성만 맞으면 execute 테스트 가능
    # -----------------------------
    ip_startup = SimpleNamespace(
        name="Burro",
        domain="AgTech",
        description="Autonomous farm robotics company",
        funding_stage="Series B",
    )

    data_startup = SimpleNamespace(
        name="Example Farm Data Platform",
        domain="AgTech",
        description="Collects farm operation data and provides analytics",
        funding_stage="Series A",
    )

    agent = TestableDataMoatAnalysisAgent()
    retriever = DummyRetriever()

    print("\n===== IP MOAT TEST =====")
    ip_result = agent.execute(ip_startup, retriever=retriever)
    print(ip_result)

    print("\n===== DATA MOAT TEST =====")
    data_result = agent.execute(data_startup, retriever=retriever)
    print(data_result)

    print("\n===== SUMMARY CHECK =====")
    print("IP Summary:", getattr(ip_result, "summary", ""))
    print("Data Summary:", getattr(data_result, "summary", ""))