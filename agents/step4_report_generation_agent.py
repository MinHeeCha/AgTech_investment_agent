"""Report Generation Agent - 한국어 중심의 PDF 투자평가 보고서 생성."""

import os
import sys
import json
from datetime import datetime
from typing import Optional, List

try:
    import anthropic
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        KeepTogether,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    REPORTLAB_AVAILABLE = True
except ImportError as e:
    REPORTLAB_AVAILABLE = False
    print(f"Warning: ReportLab import failed: {e}", file=sys.stderr)
    # fallback constants so class definitions don't fail at import time
    TA_LEFT = 0
    TA_CENTER = 1
    HexColor = lambda x: x
    ParagraphStyle = object
    black = white = None

import os
from openai import OpenAI

from models import (
    FullEvaluationResult,
    StartupProfile,
    TechnologyAnalysisResult,
    MarketabilityAnalysisResult,
    ImpactAnalysisResult,
    DataMoatAnalysisResult,
    CompetitorAnalysisResult,
    InvestmentDecision,
)
from .base_agent import BaseAgent


class ReportGenerationAgent(BaseAgent):
    """기존 분석 결과를 바탕으로 최종 한국어 보고서를 생성하는 에이전트."""

    def __init__(self):
        super().__init__(
            name="ReportGenerationAgent",
            description="한국어 중심의 비즈니스형 평가 보고서를 PDF와 텍스트로 생성",
        )
        self._openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.pdf_font_name = "Helvetica"
        self.pdf_font_name_bold = "Helvetica-Bold"
        self._init_fonts()
        
        # LLM 초기화
        if LLM_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.log_info("LLM (Anthropic) initialized successfully")
        else:
            self.client = None
            self.log_warn("Anthropic not available, LLM features disabled")

        self.color_primary       = HexColor("#17365D")   # 다크 네이비 (섹션 헤더 배경)
        self.color_primary_light = HexColor("#EAF2FF")   # 연한 파랑 (핵심포인트 박스 등)
        self.color_border        = HexColor("#2E4A6B")   # 어두운 테두리
        self.color_muted         = HexColor("#8899AA")   # 흐린 텍스트
        self.color_box_bg        = HexColor("#F7F9FC")
        self.color_section_bg    = HexColor("#1A2E45")   # 섹션 헤더 배경 (다크)
        self.color_card_bg       = HexColor("#0B1827")   # 카드/스코어 배경
        self.color_accent        = HexColor("#4ADE80")   # 라임 그린 (점수 숫자)
        self.color_subtitle      = HexColor("#60A5FA")   # 라이트 블루 (헤더 서브타이틀)
        self.color_bar_fill      = HexColor("#4ADE80")   # 바 채움 (accent 동일)
        self.color_bar_track     = HexColor("#1A3049")   # 바 배경
        self.color_white         = HexColor("#FFFFFF")
        self.color_text          = HexColor("#DDE8F2")   # 밝은 텍스트 (다크 배경용)

    # -----------------------------
    # 폰트
    # -----------------------------
    def _init_fonts(self):
        if not REPORTLAB_AVAILABLE:
            return

        try:
            candidate_fonts = [
                ("NanumGothic", "/Library/Fonts/NanumGothic.ttf", "/Library/Fonts/NanumGothicBold.ttf"),
                ("AppleGothic", "/System/Library/Fonts/Supplemental/AppleGothic.ttf", None),
                ("NanumGothic", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),
                ("NotoSansKR", "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSansKR-Bold.ttf"),
            ]

            for font_name, regular_path, bold_path in candidate_fonts:
                if regular_path and os.path.exists(regular_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, regular_path))
                        self.pdf_font_name = font_name

                        if bold_path and os.path.exists(bold_path):
                            bold_font_name = f"{font_name}-Bold"
                            pdfmetrics.registerFont(TTFont(bold_font_name, bold_path))
                            self.pdf_font_name_bold = bold_font_name
                        else:
                            self.pdf_font_name_bold = font_name

                        self.log_info(f"Registered Korean font: {font_name}")
                        return
                    except Exception as e:
                        self.log_warn(f"Failed to register {regular_path}: {e}")

            try:
                pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
                pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
                self.pdf_font_name = "HeiseiMin-W3"
                self.pdf_font_name_bold = "HeiseiKakuGo-W5"
                self.log_info("Using CID fallback fonts")
                return
            except Exception as e:
                self.log_warn(f"CID font fallback failed: {e}")

        except Exception as e:
            self.log_warn(f"Font init failed: {e}")

    # -----------------------------
    # 유틸
    # -----------------------------
    def _safe_text(self, value, default: str = "확인 필요") -> str:
        if value is None:
            return default
        if isinstance(value, str):
            v = value.strip()
            return v if v else default
        return str(value)

    def _safe_join(self, items, limit: Optional[int] = None, default: str = "해당 없음") -> str:
        if not items:
            return default
        clean = [self._safe_text(x, "").strip() for x in items if self._safe_text(x, "").strip()]
        if not clean:
            return default
        if limit is not None:
            clean = clean[:limit]
        return ", ".join(clean)

    def _safe_percent(self, value, default: str = "확인 필요") -> str:
        try:
            if value is None:
                return default
            return f"{float(value):.1%}"
        except Exception:
            return default

    def _escape(self, text: str) -> str:
        if text is None:
            return ""
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _style(
        self,
        name: str,
        parent,
        size: int = 10,
        color=None,
        bold: bool = False,
        align: int = TA_LEFT,
        leading: Optional[int] = None,
        space_after: int = 6,
        left_indent: int = 0,
    ) -> ParagraphStyle:
        return ParagraphStyle(
            name=name,
            parent=parent,
            fontName=self.pdf_font_name_bold if bold else self.pdf_font_name,
            fontSize=size,
            textColor=color or self.color_text,
            alignment=align,
            leading=leading or size + 3,
            spaceAfter=space_after,
            leftIndent=left_indent,
        )

    def _recommendation_text(self, decision) -> str:
        try:
            if decision.recommendation:
                value = decision.recommendation.value.upper()
                mapping = {
                    "INVEST":          "투자 권고",
                    "HOLD_FOR_REVIEW": "추가 검토 필요",
                    "HOLD":            "추가 검토 필요",
                    "PASS":            "투자 비권고",
                    "REJECT":          "투자 비권고",
                }
                return mapping.get(value, value)
        except Exception:
            pass
        return self._safe_text(getattr(decision, "recommendation", None), "확인 필요")

    # -----------------------------
    # 메인 실행
    # -----------------------------
    def execute(
        self,
        startup: StartupProfile,
        tech_analysis: TechnologyAnalysisResult,
        market_analysis: MarketabilityAnalysisResult,
        impact_analysis: ImpactAnalysisResult,
        data_moat_analysis: DataMoatAnalysisResult,
        competitor_analysis: CompetitorAnalysisResult,
        investment_decision: InvestmentDecision,
    ) -> FullEvaluationResult:
        self.start_execution()

        try:
            self.log_info(f"Generating report for {startup.name}")

            evaluation = FullEvaluationResult(
                startup=startup,
                technology_analysis=tech_analysis,
                marketability_analysis=market_analysis,
                impact_analysis=impact_analysis,
                data_moat_analysis=data_moat_analysis,
                competitor_analysis=competitor_analysis,
                investment_decision=investment_decision,
            )

            self._polish_evaluation_fields(evaluation)
            evaluation.report_content = self._generate_text_report(evaluation)

            if REPORTLAB_AVAILABLE:
                pdf_path = self._generate_pdf_report(evaluation)
                if pdf_path:
                    self.log_info(f"PDF report generated: {pdf_path}")

            return evaluation

        finally:
            self.end_execution()

    # -----------------------------
    # 텍스트 보고서 (LLM 활용)
    # -----------------------------
    def _generate_text_report(self, evaluation: FullEvaluationResult) -> str:
        """LLM을 호출하여 한국어 투자평가 보고서 생성"""
        try:
            # 분석 결과를 구조화된 데이터로 준비
            analysis_data = self._prepare_analysis_data(evaluation)
            
            # LLM 호출
            if self.llm is not None:
                report = self._generate_report_with_llm(analysis_data)
                self.log_info("Report generated successfully using LLM")
                return report
            else:
                # LLM 사용 불가시 템플릿 기반 보고서 생성
                self.log_info("LLM not available, using template-based report")
                return self._generate_template_report(evaluation)
                
        except Exception as e:
            self.log_warn(f"Error generating report: {e}")
            return self._generate_template_report(evaluation)
    
    def _prepare_analysis_data(self, evaluation: FullEvaluationResult) -> dict:
        """분석 결과를 LLM 프롬프트용 구조화된 데이터로 변환"""
        s = evaluation.startup
        t = evaluation.technology_analysis
        m = evaluation.marketability_analysis
        i = evaluation.impact_analysis
        d = evaluation.data_moat_analysis
        c = evaluation.competitor_analysis
        inv = evaluation.investment_decision
        
        return {
            "startup": {
                "name": self._safe_text(getattr(s, 'name', None)),
                "founded_year": self._safe_text(getattr(s, 'founded_year', None), '미상'),
                "stage": self._safe_text(getattr(s, 'stage', None), '미상'),
                "headquarters": self._safe_text(getattr(s, 'headquarters', None), '미상'),
            },
            "technology": {
                "core_technology": self._safe_text(getattr(t, 'core_technology', None)),
                "novelty_score": self._safe_percent(getattr(t, 'novelty_score', None)),
                "defensibility_score": self._safe_percent(getattr(t, 'defensibility_score', None)),
                "patents": self._safe_join(getattr(t, 'patents', None), limit=5),
                "research_papers": self._safe_join(getattr(t, 'research_papers', None), limit=5),
                "technical_keywords": self._safe_join(getattr(t, 'technical_keywords', None), limit=8),
                "summary": self._safe_text(getattr(t, 'summary', None), "자료 부족"),
            },
            "marketability": {
                "target_market_size": self._safe_text(getattr(m, 'target_market_size', None), "미확인"),
                "market_growth_potential": self._safe_percent(getattr(m, 'market_growth_potential', None)),
                "commercial_feasibility_score": self._safe_percent(getattr(m, 'commercial_feasibility_score', None)),
                "business_model": self._safe_text(getattr(m, 'business_model', None), "미확인"),
                "customer_pain_points": self._safe_join(getattr(m, 'customer_pain_points', None), limit=4),
                "adoption_barriers": self._safe_join(getattr(m, 'adoption_barriers', None), limit=4),
                "summary": self._safe_text(getattr(m, 'summary', None), "자료 부족"),
            },
            "impact": {
                "environmental_impact": self._safe_percent(getattr(i, 'environmental_impact', None)),
                "agricultural_impact": self._safe_percent(getattr(i, 'agricultural_impact', None)),
                "sustainability_focus": self._safe_join(getattr(i, 'sustainability_focus', None), limit=5),
                "efficiency_improvements": self._safe_join(getattr(i, 'efficiency_improvements', None), limit=5),
                "yield_improvement_claimed": self._safe_text(getattr(i, 'yield_improvement_claimed', None), "확인 필요"),
                "carbon_reduction_claimed": self._safe_text(getattr(i, 'carbon_reduction_claimed', None), "확인 필요"),
                "summary": self._safe_text(getattr(i, 'summary', None), "자료 부족"),
            },
            "data_moat": {
                "moat_strength_score": self._safe_percent(getattr(d, 'moat_strength_score', None)),
                "proprietary_dataset_exists": self._safe_text(getattr(d, 'proprietary_dataset_exists', None), "확인 필요"),
                "dataset_defensibility_score": self._safe_percent(getattr(d, 'dataset_defensibility_score', None)),
                "flywheel_potential_score": self._safe_percent(getattr(d, 'flywheel_potential_score', None)),
                "data_sources": self._safe_join(getattr(d, 'data_sources', None), limit=5),
                "summary": self._safe_text(getattr(d, 'summary', None), "자료 부족"),
            },
            "competitor": {
                "competitive_advantage_score": self._safe_percent(getattr(c, 'competitive_advantage_score', None)),
                "comparable_competitors": self._safe_join(getattr(c, 'comparable_competitors', None), limit=5),
                "technology_differentiation": self._safe_text(getattr(c, 'technology_differentiation', None), "확인 필요"),
                "relative_strengths": self._safe_join(getattr(c, 'relative_strengths', None), limit=4),
                "relative_weaknesses": self._safe_join(getattr(c, 'relative_weaknesses', None), limit=4),
                "summary": self._safe_text(getattr(c, 'summary', None), "자료 부족"),
            },
            "investment_decision": {
                "recommendation": self._recommendation_text(inv),
                "overall_assessment_score": self._safe_percent(getattr(inv, 'overall_assessment_score', None)),
                "confidence_score": self._safe_percent(getattr(inv, 'confidence_score', None)),
                "rationale": self._safe_text(getattr(inv, 'rationale', None), "자료 부족"),
                "key_strengths": self._safe_join(getattr(inv, 'key_strengths', None), limit=5),
                "key_risks": self._safe_join(getattr(inv, 'key_risks', None), limit=5),
                "evidence_gaps": self._safe_join(getattr(inv, 'evidence_gaps', None), limit=5),
            },
        }
    
    def _generate_report_with_llm(self, analysis_data: dict) -> str:
        """LLM을 호출하여 보고서 생성"""
        prompt = self._create_report_prompt(analysis_data)
        
        # LLM 호출
        response = self.llm.invoke(prompt)
        report_content = response.content
        
        return report_content
    
    def _create_report_prompt(self, analysis_data: dict) -> str:
        """보고서 생성을 위한 프롬프트 생성"""
        prompt = f"""다음 애그테크 스타트업 투자평가 분석 데이터를 기반으로 전문적이고 구조화된 한국어 투자평가 보고서를 작성하세요.

기업정보:
- 기업명: {analysis_data['startup']['name']}
- 설립연도: {analysis_data['startup']['founded_year']}
- 단계: {analysis_data['startup']['stage']}
- 본사: {analysis_data['startup']['headquarters']}

투자평가 결과:
- 투자 의견: {analysis_data['investment_decision']['recommendation']}
- 종합 점수: {analysis_data['investment_decision']['overall_assessment_score']}
- 신뢰도: {analysis_data['investment_decision']['confidence_score']}
- 핵심 판단: {analysis_data['investment_decision']['rationale']}

기술 분석:
- 핵심 기술: {analysis_data['technology']['core_technology']}
- 참신성: {analysis_data['technology']['novelty_score']}
- 방어력: {analysis_data['technology']['defensibility_score']}
- 특허: {analysis_data['technology']['patents']}
- 논문: {analysis_data['technology']['research_papers']}
- 기술 키워드: {analysis_data['technology']['technical_keywords']}
- 해석: {analysis_data['technology']['summary']}

시장성 분석:
- 목표시장: {analysis_data['marketability']['target_market_size']}
- 성장 가능성: {analysis_data['marketability']['market_growth_potential']}
- 사업화 가능성: {analysis_data['marketability']['commercial_feasibility_score']}
- 비즈니스 모델: {analysis_data['marketability']['business_model']}
- 고객 문제점: {analysis_data['marketability']['customer_pain_points']}
- 도입 장벽: {analysis_data['marketability']['adoption_barriers']}
- 해석: {analysis_data['marketability']['summary']}

임팩트 분석:
- 환경적 영향: {analysis_data['impact']['environmental_impact']}
- 농업적 영향: {analysis_data['impact']['agricultural_impact']}
- 지속가능성 초점: {analysis_data['impact']['sustainability_focus']}
- 효율 개선: {analysis_data['impact']['efficiency_improvements']}
- 수확량 개선: {analysis_data['impact']['yield_improvement_claimed']}
- 탄소 저감: {analysis_data['impact']['carbon_reduction_claimed']}
- 해석: {analysis_data['impact']['summary']}

데이터 해자 분석:
- 해자 강도: {analysis_data['data_moat']['moat_strength_score']}
- 독점 데이터셋: {analysis_data['data_moat']['proprietary_dataset_exists']}
- 방어력: {analysis_data['data_moat']['dataset_defensibility_score']}
- 축적 효과: {analysis_data['data_moat']['flywheel_potential_score']}
- 데이터 원천: {analysis_data['data_moat']['data_sources']}
- 해석: {analysis_data['data_moat']['summary']}

경쟁력 분석:
- 경쟁우위: {analysis_data['competitor']['competitive_advantage_score']}
- 비교 경쟁사: {analysis_data['competitor']['comparable_competitors']}
- 기술 차별성: {analysis_data['competitor']['technology_differentiation']}
- 상대적 강점: {analysis_data['competitor']['relative_strengths']}
- 상대적 약점: {analysis_data['competitor']['relative_weaknesses']}
- 해석: {analysis_data['competitor']['summary']}

투자심사 평가:
- 주요 강점: {analysis_data['investment_decision']['key_strengths']}
- 주요 리스크: {analysis_data['investment_decision']['key_risks']}
- 증거 공백: {analysis_data['investment_decision']['evidence_gaps']}

다음 형식으로 보고서를 작성하세요:

╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                             애그테크 스타트업 투자 평가 보고서                
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─ [기업명] / [단계] / [본사] ─┐
└────────────────────────────────────────────────────────────────────────────┘

┌─ 투자평가 점수카드 ─⋯┐
│
│  투자 의견: [의견]  │ 종합 점수: [점수]  │ 신뢰도: [신뢰도]  │
│
└────────────────────────────────────────────────────────────────────────────┘

┌─ 투자 판단 핵심 포인트 ─┐
│
│ [핵심 판단 내용]
│
└────────────────────────────────────────────────────────────────────────────┘

┌─ 기업 개요 ─┐
│ 기업명: [기업명]  │ 설립연도: [연도]  │
│ 단계: [단계]  │ 본사: [본사]  │
└────────────────────────────────────────────────────────────────────────────┘

┌─ 5대 분석 영역 점수 요약 ─┐
│ 기술: [점수]  │ 시장성: [점수]  │ 임팩트: [점수]  │ 데이터해자: [점수]  │ 경쟁력: [점수]  │
└────────────────────────────────────────────────────────────────────────────┘

┌─ 기술 분석 ─┐
│
│ 핵심 기술    : [기술]
│ 참신성       : [점수]
│ 방어력       : [점수]
│ 특허         : [특허]
│ 논문         : [논문]
│ 기술 키워드  : [키워드]
│ 핵심 해석    : [해석]
│
└────────────────────────────────────────────────────────────────────────────┘

[시장성 분석, 임팩트 분석, 데이터 해자 분석, 경쟁력 분석도 동일한 형식으로 작성]

┌─ 투자심사 평가 요소 ─┐
│
│ [주요 강점]
│ [주요 리스크]
│ [증거 공백]
│
└────────────────────────────────────────────────────────────────────────────┘

───────────────────────────────────────────────────────────────────────────────
보고서 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
───────────────────────────────────────────────────────────────────────────────
"""
        return prompt
    
    def _generate_template_report(self, evaluation: FullEvaluationResult) -> str:
        """LLM 없을 때 사용할 템플릿 기반 보고서 생성"""
        s = evaluation.startup
        t = evaluation.technology_analysis
        m = evaluation.marketability_analysis
        i = evaluation.impact_analysis
        d = evaluation.data_moat_analysis
        c = evaluation.competitor_analysis
        inv = evaluation.investment_decision

        lines = []
        lines.append("=" * 80)
        lines.append("애그테크 스타트업 투자 평가 보고서")
        lines.append("=" * 80)
        lines.append("")
        lines.append("[종합 요약]")
        lines.append(f"기업명: {self._safe_text(getattr(s, 'name', None))}")
        lines.append(f"설립연도: {self._safe_text(getattr(s, 'founded_year', None), '미상')}")
        lines.append(f"단계: {self._safe_text(getattr(s, 'stage', None), '미상')}")
        lines.append(f"본사: {self._safe_text(getattr(s, 'headquarters', None), '미상')}")
        lines.append(f"투자 의견: {self._recommendation_text(inv)}")
        lines.append(f"종합 점수: {self._safe_percent(getattr(inv, 'overall_assessment_score', None))}")
        lines.append(f"판단 신뢰도: {self._safe_percent(getattr(inv, 'confidence_score', None))}")
        lines.append(f"핵심 판단: {self._safe_text(getattr(inv, 'rationale', None), '자료 부족')}")
        lines.append("")
        lines.append("[기술 분석]")
        lines.append(f"핵심 기술: {self._safe_text(getattr(t, 'core_technology', None))}")
        lines.append(f"기술 참신성: {self._safe_percent(getattr(t, 'novelty_score', None))}")
        lines.append(f"방어력: {self._safe_percent(getattr(t, 'defensibility_score', None))}")
        lines.append(f"특허: {self._safe_join(getattr(t, 'patents', None), limit=5)}")
        lines.append(f"논문: {self._safe_join(getattr(t, 'research_papers', None), limit=5)}")
        lines.append(f"기술 키워드: {self._safe_join(getattr(t, 'technical_keywords', None), limit=8)}")
        lines.append("")
        lines.append("[투자 판단]")
        lines.append(f"주요 강점: {self._safe_join(getattr(inv, 'key_strengths', None), limit=5)}")
        lines.append(f"주요 리스크: {self._safe_join(getattr(inv, 'key_risks', None), limit=5)}")
        lines.append(f"증거 공백: {self._safe_join(getattr(inv, 'evidence_gaps', None), limit=5)}")
        lines.append("")
        lines.append(f"생성 시각: {datetime.now().isoformat()}")

        return "\n".join(lines)

    # -----------------------------
    # LLM 필드 다듬기
    # -----------------------------
    def _polish_evaluation_fields(self, evaluation: FullEvaluationResult) -> None:
        """
        PDF/txt에 직접 노출되는 텍스트 필드들을 LLM으로 다듬어 in-place 업데이트.
        실패 시 원본 유지.
        """
        t   = evaluation.technology_analysis
        m   = evaluation.marketability_analysis
        i   = evaluation.impact_analysis
        d   = evaluation.data_moat_analysis
        c   = evaluation.competitor_analysis
        inv = evaluation.investment_decision
        startup_name = getattr(evaluation.startup, "name", "Unknown")

        prompt = f"""당신은 AgTech 전문 VC 애널리스트입니다.
아래 항목들을 전문 투자 보고서 수준의 한국어로 다듬어주세요.

규칙:
- 원본 수치와 사실을 유지하되 표현을 전문적으로 개선
- 영어 표현은 한국어로 번역 (고유명사·지표·수치 제외)
- *_summary 필드: "X점 | Y점" 같은 파이프 구분 나열 형식을 없애고, 투자 보고서처럼 자연스러운 서술 문장 2~3개로 작성
- core_technology: 기술의 핵심을 한 문장 명사형으로 간결하게 요약 (예: "드론·위성 이미지 기반 정밀 작물 모니터링 플랫폼")
- relative_strengths, relative_weaknesses, key_strengths, key_risks, evidence_gaps: 반드시 한국어로 작성. 각 항목은 투자자가 바로 읽을 수 있는 명확한 한국어 문장으로 다듬기. 영어 원문이 있으면 반드시 번역할 것. 숫자 뒤 괄호 표기(예: (0.80), (11.00))는 자연스러운 서술로 흡수하거나 제거할 것.
- rationale은 4~5문장의 투자 의견 단락으로 작성:
  "[기업명]은 [핵심 기술/강점 서술]. [시장 기회 및 성장 동력]. [경쟁 포지션 또는 차별성]. [주요 리스크 언급]. [투자 권고 및 권장 규모]."
- JSON으로만 응답 (키 그대로 유지)

## 기업명
{startup_name}

## 다듬을 항목
{{
  "core_technology": {t.core_technology!r},
  "tech_summary": {t.summary!r},
  "market_summary": {m.summary!r},
  "impact_summary": {i.summary!r},
  "moat_summary": {d.summary!r},
  "competitor_summary": {c.summary!r},
  "tech_differentiation": {c.technology_differentiation!r},
  "relative_strengths": {c.relative_strengths!r},
  "relative_weaknesses": {c.relative_weaknesses!r},
  "key_strengths": {inv.key_strengths!r},
  "key_risks": {inv.key_risks!r},
  "evidence_gaps": {inv.evidence_gaps!r},
  "rationale": {inv.rationale!r}
}}"""

        try:
            response = self._openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            import json
            polished = json.loads(response.choices[0].message.content)

            if polished.get("core_technology"):     t.core_technology = polished["core_technology"]
            if polished.get("tech_summary"):       t.summary = polished["tech_summary"]
            if polished.get("market_summary"):     m.summary = polished["market_summary"]
            if polished.get("impact_summary"):     i.summary = polished["impact_summary"]
            if polished.get("moat_summary"):       d.summary = polished["moat_summary"]
            if polished.get("competitor_summary"): c.summary = polished["competitor_summary"]
            if polished.get("tech_differentiation"):  c.technology_differentiation = polished["tech_differentiation"]
            if polished.get("relative_strengths") and isinstance(polished["relative_strengths"], list):
                c.relative_strengths = polished["relative_strengths"]
            if polished.get("relative_weaknesses") and isinstance(polished["relative_weaknesses"], list):
                c.relative_weaknesses = polished["relative_weaknesses"]
            if polished.get("key_strengths") and isinstance(polished["key_strengths"], list):
                inv.key_strengths = polished["key_strengths"]
            if polished.get("key_risks") and isinstance(polished["key_risks"], list):
                inv.key_risks = polished["key_risks"]
            if polished.get("evidence_gaps") and isinstance(polished["evidence_gaps"], list):
                inv.evidence_gaps = polished["evidence_gaps"]
            if polished.get("rationale"):          inv.rationale = polished["rationale"]

            self.log_info(f"[{startup_name}] 텍스트 필드 LLM 다듬기 완료")
        except Exception as e:
            self.log_warning(f"LLM 필드 다듬기 실패 ({e}), 원본 유지")

    # -----------------------------
    # PDF 생성
    # -----------------------------
    def _generate_pdf_report(self, evaluation: FullEvaluationResult) -> Optional[str]:
        try:
            startup_name = self._safe_text(getattr(evaluation.startup, "name", None), "startup")
            safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in startup_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = os.path.abspath(f"{safe_name}_투자평가보고서_{timestamp}.pdf")

            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=1.4 * cm,
                leftMargin=1.4 * cm,
                topMargin=1.2 * cm,
                bottomMargin=1.2 * cm,
            )

            styles = getSampleStyleSheet()
            story = []

            story.extend(self._build_header_block(evaluation, styles))
            story.append(Spacer(1, 0.35 * cm))
            story.extend(self._build_score_cards(evaluation, styles))
            story.append(Spacer(1, 0.25 * cm))
            story.extend(self._build_key_message_box(evaluation, styles))
            story.append(Spacer(1, 0.25 * cm))
            story.extend(self._build_company_overview(evaluation, styles))
            story.append(Spacer(1, 0.25 * cm))
            story.extend(self._build_analysis_summary_table(evaluation, styles))
            story.append(Spacer(1, 0.25 * cm))
            story.extend(self._build_toc(styles))
            story.append(Spacer(1, 0.25 * cm))

            story.extend(self._build_section_block(
                "기술 분석",
                [
                    ("핵심 기술", self._safe_text(getattr(evaluation.technology_analysis, "core_technology", None))),
                    ("기술 참신성", self._safe_percent(getattr(evaluation.technology_analysis, "novelty_score", None))),
                    ("기술 방어력", self._safe_percent(getattr(evaluation.technology_analysis, "defensibility_score", None))),
                    ("특허", self._safe_join(getattr(evaluation.technology_analysis, "patents", None), limit=5)),
                    ("논문", self._safe_join(getattr(evaluation.technology_analysis, "research_papers", None), limit=5)),
                    ("기술 키워드", self._safe_join(getattr(evaluation.technology_analysis, "technical_keywords", None), limit=8)),
                    ("핵심 해석", self._safe_text(getattr(evaluation.technology_analysis, "summary", None), "자료 부족")),
                ],
                styles
            ))

            story.extend(self._build_section_block(
                "시장성 분석",
                [
                    ("목표 시장", self._safe_text(getattr(evaluation.marketability_analysis, "target_market_size", None), "미확인")),
                    ("성장 가능성", self._safe_percent((lambda v: v / 11.0 if v is not None else None)(getattr(evaluation.marketability_analysis, "market_growth_potential", None)))),
                    ("사업화 가능성", self._safe_percent((lambda v: v / 25.0 if v is not None else None)(getattr(evaluation.marketability_analysis, "commercial_feasibility_score", None)))),
                    ("비즈니스 모델", self._safe_text(getattr(evaluation.marketability_analysis, "business_model", None), "미확인")),
                    ("고객 문제", self._safe_join(getattr(evaluation.marketability_analysis, "customer_pain_points", None), limit=4)),
                    ("도입 장벽", self._safe_join(getattr(evaluation.marketability_analysis, "adoption_barriers", None), limit=4)),
                    ("핵심 해석", self._safe_text(getattr(evaluation.marketability_analysis, "summary", None), "자료 부족")),
                ],
                styles
            ))

            story.extend(self._build_section_block(
                "임팩트 분석",
                [
                    ("환경적 영향", self._safe_percent(getattr(evaluation.impact_analysis, "environmental_impact", None))),
                    ("농업적 영향", self._safe_percent(getattr(evaluation.impact_analysis, "agricultural_impact", None))),
                    ("지속가능성 초점", self._safe_join(getattr(evaluation.impact_analysis, "sustainability_focus", None), limit=5)),
                    ("효율 개선", self._safe_join(getattr(evaluation.impact_analysis, "efficiency_improvements", None), limit=5)),
                    ("수확량 개선", self._safe_text(getattr(evaluation.impact_analysis, "yield_improvement_claimed", None), "확인 필요")),
                    ("탄소 저감", self._safe_text(getattr(evaluation.impact_analysis, "carbon_reduction_claimed", None), "확인 필요")),
                    ("핵심 해석", self._safe_text(getattr(evaluation.impact_analysis, "summary", None), "자료 부족")),
                ],
                styles
            ))

            story.extend(self._build_section_block(
                "데이터 해자 분석",
                [
                    ("해자 강도", self._safe_percent(getattr(evaluation.data_moat_analysis, "moat_strength_score", None))),
                    ("독점 데이터셋", self._safe_text(getattr(evaluation.data_moat_analysis, "proprietary_dataset_exists", None), "확인 필요")),
                    ("데이터 방어력", self._safe_percent(getattr(evaluation.data_moat_analysis, "dataset_defensibility_score", None))),
                    ("데이터 축적 효과", self._safe_percent(getattr(evaluation.data_moat_analysis, "flywheel_potential_score", None))),
                    ("데이터 원천", self._safe_join(getattr(evaluation.data_moat_analysis, "data_sources", None), limit=5)),
                    ("핵심 해석", self._safe_text(getattr(evaluation.data_moat_analysis, "summary", None), "자료 부족")),
                ],
                styles
            ))

            story.extend(self._build_section_block(
                "경쟁력 분석",
                [
                    ("경쟁우위", self._safe_percent(getattr(evaluation.competitor_analysis, "competitive_advantage_score", None))),
                    ("비교 경쟁사", self._safe_join(getattr(evaluation.competitor_analysis, "comparable_competitors", None), limit=5)),
                    ("기술 차별성", self._safe_text(getattr(evaluation.competitor_analysis, "technology_differentiation", None), "확인 필요")),
                    ("상대적 강점", self._safe_join(getattr(evaluation.competitor_analysis, "relative_strengths", None), limit=4)),
                    ("상대적 약점", self._safe_join(getattr(evaluation.competitor_analysis, "relative_weaknesses", None), limit=4)),
                    ("핵심 해석", self._safe_text(getattr(evaluation.competitor_analysis, "summary", None), "자료 부족")),
                ],
                styles
            ))

            story.extend(self._build_risk_strength_gap_boxes(evaluation, styles))
            story.append(Spacer(1, 0.25 * cm))
            story.extend(self._build_references(evaluation, styles))
            story.append(Spacer(1, 0.2 * cm))
            story.extend(self._build_footer(evaluation, styles))

            page_bg = self.color_card_bg  # 다크 배경색

            def _draw_dark_bg(canvas, doc):
                canvas.saveState()
                canvas.setFillColor(page_bg)
                canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
                canvas.restoreState()

            doc.build(story, onFirstPage=_draw_dark_bg, onLaterPages=_draw_dark_bg)
            return pdf_path

        except Exception as e:
            self.log_warn(f"PDF generation failed: {e}")
            return None

    # -----------------------------
    # LLM 서술 블록
    # -----------------------------
    def _build_llm_narrative_block(self, report_content: str, styles):
        """LLM이 다듬은 보고서 텍스트를 PDF 섹션으로 렌더링."""
        section_title = self._style("llm_title", styles["Heading2"], size=11, color=self.color_primary, bold=True, leading=14, space_after=6)
        body_style = self._style("llm_body", styles["Normal"], size=9, color=self.color_text, leading=14, space_after=4)

        elements = [Paragraph("AI 종합 분석 의견", section_title), Spacer(1, 0.15 * cm)]

        for line in report_content.split("\n"):
            line = line.strip()
            if not line:
                elements.append(Spacer(1, 0.1 * cm))
                continue
            # 헤더 라인 (##, # 으로 시작) → 굵게
            if line.startswith("##") or line.startswith("#"):
                header_style = self._style("llm_h", styles["Normal"], size=10, color=self.color_primary, bold=True, leading=14, space_after=2)
                elements.append(Paragraph(self._escape(line.lstrip("#").strip()), header_style))
            else:
                elements.append(Paragraph(self._escape(line), body_style))

        box = Table([[elements]], colWidths=[18.2 * cm])
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.color_section_bg),
            ("BOX",        (0, 0), (-1, -1), 0.5, self.color_border),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ]))
        return [box]

    # -----------------------------
    # PDF 구성요소
    # -----------------------------
    def _build_header_block(self, evaluation, styles):
        startup = evaluation.startup
        name    = self._safe_text(getattr(startup, "name", None))
        stage   = self._safe_text(getattr(startup, "stage", None), "미상")
        hq      = self._safe_text(getattr(startup, "headquarters", None), "미상")

        company_style  = self._style("hdr_company",  styles["Normal"], size=26, color=self.color_white,  bold=True,  align=TA_CENTER, leading=30, space_after=4)
        sub_style      = self._style("hdr_sub",      styles["Normal"], size=10, color=self.color_subtitle, bold=False, align=TA_CENTER, leading=13, space_after=0)
        caption_style  = self._style("hdr_caption",  styles["Normal"], size=8,  color=self.color_muted,  bold=False, align=TA_CENTER, leading=11, space_after=0)

        box = Table(
            [[Paragraph(self._escape(name), company_style)],
             [Paragraph(self._escape(f"{stage}  ·  {hq}  ·"), sub_style)],
             [Paragraph("기존 분석 결과를 종합한 투자 검토용 개괄 보고서", caption_style)]],
            colWidths=[18.2 * cm],
        )
        box.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), self.color_card_bg),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("TOPPADDING",    (0, 0), (-1, 0),  18),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
            ("TOPPADDING",    (0, 1), (-1, -1),  4),
            ("BOTTOMPADDING", (0, 0), (-1, -2),  2),
        ]))
        return [box]

    def _build_score_cards(self, evaluation, styles):
        inv = evaluation.investment_decision

        label = self._style("card_label", styles["Normal"], size=8,  color=self.color_muted,  align=TA_CENTER, leading=10, space_after=2)
        value = self._style("card_value", styles["Normal"], size=22, color=self.color_accent, bold=True, align=TA_CENTER, leading=26, space_after=0)

        recommendation = self._recommendation_text(inv)
        overall        = self._safe_percent(getattr(inv, "overall_assessment_score", None))
        confidence     = self._safe_percent(getattr(inv, "confidence_score", None))

        data = [
            [Paragraph("투자 의견", label),            Paragraph("종합 점수", label),         Paragraph("판단 신뢰도", label)],
            [Paragraph(self._escape(recommendation), value), Paragraph(self._escape(overall), value), Paragraph(self._escape(confidence), value)],
        ]

        table = Table(data, colWidths=[6.05 * cm, 6.05 * cm, 6.05 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.color_card_bg),
            ("GRID",       (0, 0), (-1, -1), 0.5, self.color_border),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        return [table]

    def _build_key_message_box(self, evaluation, styles):
        inv = evaluation.investment_decision
        body = self._style("keymsg", styles["Normal"], size=10, color=self.color_text, leading=14, space_after=0)

        text = (
            f"<b>투자 판단 핵심 포인트</b><br/>"
            f"{self._escape(self._safe_text(getattr(inv, 'rationale', None), '자료 부족'))}"
        )

        table = Table([[Paragraph(text, body)]], colWidths=[18.2 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, -1), self.color_card_bg),
            ("LINEBEFORE",  (0, 0), (0, -1),  4, self.color_accent),
            ("BOX",         (0, 0), (-1, -1),  0.5, self.color_border),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING",(0, 0), (-1, -1), 12),
            ("TOPPADDING",  (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING",(0,0), (-1, -1), 10),
        ]))
        return [table]

    def _build_company_overview(self, evaluation, styles):
        s = evaluation.startup
        label = self._style("ov_label", styles["Normal"], size=9, color=self.color_muted, bold=True, leading=11)
        value = self._style("ov_value", styles["Normal"], size=10, color=self.color_text, leading=13)

        data = [
            [Paragraph("기업명", label), Paragraph(self._escape(self._safe_text(getattr(s, "name", None))), value),
             Paragraph("설립연도", label), Paragraph(self._escape(self._safe_text(getattr(s, "founded_year", None), "미상")), value)],
            [Paragraph("단계", label), Paragraph(self._escape(self._safe_text(getattr(s, "stage", None), "미상")), value),
             Paragraph("본사", label), Paragraph(self._escape(self._safe_text(getattr(s, "headquarters", None), "미상")), value)],
        ]

        table = Table(data, colWidths=[2.3 * cm, 6.8 * cm, 2.3 * cm, 6.8 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.color_card_bg),
            ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
            ("GRID", (0, 0), (-1, -1), 0.5, self.color_border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (0, -1), self.color_section_bg),
            ("BACKGROUND", (2, 0), (2, -1), self.color_section_bg),
        ]))
        return [table]

    def _build_analysis_summary_table(self, evaluation, styles):
        """레퍼런스 PDF 스타일 수평 바 차트."""
        t = evaluation.technology_analysis
        m = evaluation.marketability_analysis
        i = evaluation.impact_analysis
        d = evaluation.data_moat_analysis
        c = evaluation.competitor_analysis

        header_style = self._style("bar_header", styles["Normal"], size=9,  color=self.color_white, bold=True,  leading=11, space_after=4)
        cat_style    = self._style("bar_cat",    styles["Normal"], size=9,  color=self.color_white, bold=False, leading=11, space_after=0)
        pct_style    = self._style("bar_pct",    styles["Normal"], size=9,  color=self.color_accent, bold=True, leading=11, space_after=0)

        BAR_TOTAL = 9.0 * cm   # 바 전체 너비

        def _bar_row(label: str, score: float):
            fill_w = BAR_TOTAL * min(max(score, 0.0), 1.0)
            track_w = BAR_TOTAL - fill_w
            bar_parts = []
            if fill_w > 0:
                bar_parts.append(Table([[""]], colWidths=[fill_w],
                    rowHeights=[0.35 * cm]))
                bar_parts[-1].setStyle(TableStyle([("BACKGROUND", (0,0),(-1,-1), self.color_bar_fill)]))
            if track_w > 0:
                bar_parts.append(Table([[""]], colWidths=[track_w],
                    rowHeights=[0.35 * cm]))
                bar_parts[-1].setStyle(TableStyle([("BACKGROUND", (0,0),(-1,-1), self.color_bar_track)]))
            bar_cell = Table([bar_parts], colWidths=[fill_w if fill_w>0 else None, track_w if track_w>0 else None])
            bar_cell.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                                           ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
            return [Paragraph(self._escape(label), cat_style), bar_cell, Paragraph(f"{score:.1%}", pct_style)]

        impact_score = float(getattr(i, "total_impact_score", 0) or 0) / 15.0
        items = [
            ("기술력",    float(getattr(t, "novelty_score", 0) or 0)),
            ("시장성",    float(getattr(m, "commercial_feasibility_score", 0) or 0) / 25.0),
            ("임팩트",    impact_score),
            ("데이터 해자", float(getattr(d, "moat_strength_score", 0) or 0)),
            ("경쟁력",    float(getattr(c, "competitive_advantage_score", 0) or 0)),
        ]

        title_row = [Paragraph("◆  평가 항목별 점수", header_style), "", ""]
        rows = [title_row] + [_bar_row(lbl, score) for lbl, score in items]

        table = Table(rows, colWidths=[3.5 * cm, BAR_TOTAL, 2.2 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), self.color_card_bg),
            ("SPAN",          (0, 0), (-1, 0)),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return [table]

    def _build_section_block(self, title: str, rows: List[tuple], styles):
        title_style = self._style(
            f"title_{title}",
            styles["Heading2"],
            size=11,
            color=self.color_white,
            bold=True,
            leading=14,
            space_after=0,
        )
        label = self._style(f"label_{title}", styles["Normal"], size=8, color=self.color_muted, bold=True, leading=10)
        value = self._style(f"value_{title}", styles["Normal"], size=9, color=self.color_text, leading=12)

        title_bar = Table([[Paragraph(f"◆  {self._escape(title)}", title_style)]], colWidths=[18.2 * cm])
        title_bar.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), self.color_section_bg),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))

        table_rows = []
        for k, v in rows:
            table_rows.append([
                Paragraph(self._escape(k), label),
                Paragraph(self._escape(v), value),
            ])

        detail_table = Table(table_rows, colWidths=[4.0 * cm, 14.2 * cm])
        detail_table.setStyle(TableStyle([
            ("BOX",        (0, 0), (-1, -1), 0.6, self.color_border),
            ("GRID",       (0, 0), (-1, -1), 0.4, self.color_border),
            ("BACKGROUND", (0, 0), (-1, -1), self.color_card_bg),
            ("BACKGROUND", (0, 0), (0,  -1), self.color_section_bg),
            ("VALIGN",     (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ]))

        return [Spacer(1, 0.18 * cm), KeepTogether([title_bar, Spacer(1, 0.08 * cm), detail_table])]

    def _safe_bullets(self, items, limit=None, default="해당 없음") -> str:
        """리스트 항목을 bullet point HTML 문자열로 변환 (항목별 escape 적용)."""
        if not items:
            return default
        clean = [self._safe_text(x, "").strip() for x in items if self._safe_text(x, "").strip()]
        if not clean:
            return default
        if limit:
            clean = clean[:limit]
        return "<br/>".join(f"• {self._escape(item)}" for item in clean)

    def _build_risk_strength_gap_boxes(self, evaluation, styles):
        inv = evaluation.investment_decision
        title_s = self._style("rsg_title_s", styles["Normal"], size=9, color=self.color_accent,  bold=True, leading=12, space_after=4)
        title_r = self._style("rsg_title_r", styles["Normal"], size=9, color=HexColor("#F87171"), bold=True, leading=12, space_after=4)
        title_g = self._style("rsg_title_g", styles["Normal"], size=9, color=self.color_muted,   bold=True, leading=12, space_after=4)
        body    = self._style("rsg_body",    styles["Normal"], size=9, color=self.color_text,    leading=13)

        strengths_t = Paragraph("주요 강점",  title_s)
        risks_t     = Paragraph("주요 리스크", title_r)
        gaps_t      = Paragraph("증거 공백",  title_g)

        strengths_b = Paragraph(self._safe_bullets(getattr(inv, "key_strengths",  None), limit=5), body)
        risks_b     = Paragraph(self._safe_bullets(getattr(inv, "key_risks",       None), limit=5), body)
        gaps_b      = Paragraph(self._safe_bullets(getattr(inv, "evidence_gaps",   None), limit=5), body)

        data = [[strengths_t, risks_t, gaps_t], [strengths_b, risks_b, gaps_b]]
        table = Table(data, colWidths=[6.05 * cm, 6.05 * cm, 6.05 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), self.color_card_bg),
            ("LINEABOVE",     (0, 0), (0, 0),   3, self.color_accent),
            ("LINEABOVE",     (1, 0), (1, 0),   3, HexColor("#F87171")),
            ("LINEABOVE",     (2, 0), (2, 0),   3, self.color_muted),
            ("BOX",           (0, 0), (-1, -1), 0.5, self.color_border),
            ("GRID",          (0, 0), (-1, -1), 0.5, self.color_border),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        return [table]

    def _build_toc(self, styles):
        """목차 블록."""
        header_style = self._style("toc_hdr", styles["Normal"], size=9,  color=self.color_white, bold=True,  leading=11, space_after=4)
        num_style    = self._style("toc_num", styles["Normal"], size=9,  color=self.color_muted, bold=False, leading=11, space_after=0)
        item_style   = self._style("toc_itm", styles["Normal"], size=9,  color=self.color_text,  bold=False, leading=11, space_after=0)

        sections = [
            ("01", "투자 의견 요약"),
            ("02", "기업 기본 정보"),
            ("03", "평가 항목별 점수"),
            ("04", "기술 분석"),
            ("05", "시장성 분석"),
            ("06", "임팩트 분석"),
            ("07", "데이터 해자 분석"),
            ("08", "경쟁력 분석"),
            ("09", "종합 검토"),
            ("10", "참고 자료"),
        ]

        title_bar = Table([[Paragraph("◆  목  차", header_style)]], colWidths=[18.2 * cm])
        title_bar.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), self.color_section_bg),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))

        rows = []
        for num, name in sections:
            rows.append([
                Paragraph(num, num_style),
                Paragraph(self._escape(name), item_style),
            ])

        toc_table = Table(rows, colWidths=[1.2 * cm, 17.0 * cm])
        toc_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), self.color_card_bg),
            ("BACKGROUND",    (0, 0), (0, -1),  self.color_section_bg),
            ("LINEBELOW",     (0, 0), (-1, -2), 0.3, self.color_border),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (0, -1),  12),
            ("LEFTPADDING",   (1, 0), (1, -1),  8),
        ]))

        return [Spacer(1, 0.18 * cm), KeepTogether([title_bar, Spacer(1, 0.08 * cm), toc_table])]

    def _build_references(self, evaluation, styles):
        """참고 자료 블록 — evidence 에서 source_document 수집."""
        header_style = self._style("ref_hdr", styles["Normal"], size=9, color=self.color_white, bold=True,  leading=11, space_after=4)
        num_style    = self._style("ref_num", styles["Normal"], size=8, color=self.color_muted, bold=False, leading=11, space_after=0)
        src_style    = self._style("ref_src", styles["Normal"], size=8, color=self.color_text,  bold=False, leading=12, space_after=0)

        sources = []
        seen = set()
        analyses = [
            evaluation.technology_analysis,
            evaluation.marketability_analysis,
            evaluation.impact_analysis,
            evaluation.data_moat_analysis,
            evaluation.competitor_analysis,
            evaluation.investment_decision,
        ]
        for analysis in analyses:
            for ev in getattr(analysis, "evidence", []):
                src = (getattr(ev, "source_document", None) or "").strip()
                if src and src not in seen:
                    seen.add(src)
                    sources.append(src)

        if not sources:
            sources = ["참고 문서 정보 없음"]

        title_bar = Table([[Paragraph("◆  참고 자료", header_style)]], colWidths=[18.2 * cm])
        title_bar.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), self.color_section_bg),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))

        rows = []
        for i, src in enumerate(sources, 1):
            rows.append([
                Paragraph(f"[{i:02d}]", num_style),
                Paragraph(self._escape(src), src_style),
            ])

        ref_table = Table(rows, colWidths=[1.2 * cm, 17.0 * cm])
        ref_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), self.color_card_bg),
            ("BACKGROUND",    (0, 0), (0, -1),  self.color_section_bg),
            ("LINEBELOW",     (0, 0), (-1, -2), 0.3, self.color_border),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (0, -1),  12),
            ("LEFTPADDING",   (1, 0), (1, -1),  8),
        ]))

        return [Spacer(1, 0.18 * cm), KeepTogether([title_bar, Spacer(1, 0.08 * cm), ref_table])]

    def _build_footer(self, evaluation, styles):
        footer = self._style("footer", styles["Normal"], size=8, color=self.color_muted, align=TA_CENTER, leading=10, space_after=0)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [Paragraph(self._escape(f"보고서 생성 시각: {ts}"), footer)]

    # -----------------------------
    # 텍스트 저장
    # -----------------------------
    def save_report(self, evaluation: FullEvaluationResult, filepath: str) -> bool:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self._safe_text(getattr(evaluation, "report_content", None), ""))
            self.log_info(f"Report saved to {filepath}")
            return True
        except Exception as e:
            self.log_warn(f"Failed to save report: {e}")
            return False