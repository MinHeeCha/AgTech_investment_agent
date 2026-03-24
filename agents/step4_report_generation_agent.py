# """Report Generation Agent - Creates polished Korean PDF evaluation reports."""

# import os
# import sys
# from datetime import datetime
# from typing import Optional, List

# try:
#     from reportlab.lib.pagesizes import A4
#     from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
#     from reportlab.lib.units import cm
#     from reportlab.lib.colors import HexColor, black, white
#     from reportlab.lib.enums import TA_LEFT, TA_CENTER
#     from reportlab.platypus import (
#         SimpleDocTemplate,
#         Table,
#         TableStyle,
#         Paragraph,
#         Spacer,
#         KeepTogether,
#     )
#     from reportlab.pdfbase import pdfmetrics
#     from reportlab.pdfbase.ttfonts import TTFont
#     from reportlab.pdfbase.cidfonts import UnicodeCIDFont

#     REPORTLAB_AVAILABLE = True
# except ImportError as e:
#     REPORTLAB_AVAILABLE = False
#     print(f"Warning: ReportLab import failed: {e}", file=sys.stderr)

# from models import (
#     FullEvaluationResult,
#     StartupProfile,
#     TechnologyAnalysisResult,
#     MarketabilityAnalysisResult,
#     ImpactAnalysisResult,
#     DataMoatAnalysisResult,
#     CompetitorAnalysisResult,
#     InvestmentDecision,
# )
# from .base_agent import BaseAgent


# class ReportGenerationAgent(BaseAgent):
#     """Final reporting layer: assembles analysis results into text/PDF reports."""

#     def __init__(self):
#         super().__init__(
#             name="ReportGenerationAgent",
#             description="Generates polished Korean business evaluation reports in PDF and text formats",
#         )
#         self.pdf_font_name = "Helvetica"
#         self.pdf_font_name_bold = "Helvetica-Bold"
#         self._init_fonts()

#         self.color_primary = HexColor("#17365D")
#         self.color_primary_light = HexColor("#EAF2FF")
#         self.color_border = HexColor("#D7DDE5")
#         self.color_text = HexColor("#222222")
#         self.color_muted = HexColor("#666666")
#         self.color_success = HexColor("#1F6E43")
#         self.color_warning = HexColor("#8A6D1D")
#         self.color_risk = HexColor("#A94442")
#         self.color_box_bg = HexColor("#F7F9FC")
#         self.color_section_bg = HexColor("#F3F6FA")

#     # -----------------------------
#     # Font
#     # -----------------------------
#     def _init_fonts(self):
#         if not REPORTLAB_AVAILABLE:
#             return

#         try:
#             candidate_fonts = [
#                 ("NanumGothic", "/Library/Fonts/NanumGothic.ttf", "/Library/Fonts/NanumGothicBold.ttf"),
#                 ("AppleGothic", "/System/Library/Fonts/Supplemental/AppleGothic.ttf", None),
#                 ("NanumGothic", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),
#                 ("NotoSansKR", "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSansKR-Bold.ttf"),
#             ]

#             for font_name, regular_path, bold_path in candidate_fonts:
#                 if regular_path and os.path.exists(regular_path):
#                     try:
#                         pdfmetrics.registerFont(TTFont(font_name, regular_path))
#                         self.pdf_font_name = font_name

#                         if bold_path and os.path.exists(bold_path):
#                             bold_font_name = f"{font_name}-Bold"
#                             pdfmetrics.registerFont(TTFont(bold_font_name, bold_path))
#                             self.pdf_font_name_bold = bold_font_name
#                         else:
#                             self.pdf_font_name_bold = font_name

#                         self.log_info(f"Registered Korean font: {font_name}")
#                         return
#                     except Exception as e:
#                         self.log_warn(f"Failed to register {regular_path}: {e}")

#             try:
#                 pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
#                 pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
#                 self.pdf_font_name = "HeiseiMin-W3"
#                 self.pdf_font_name_bold = "HeiseiKakuGo-W5"
#                 self.log_info("Using CID fallback fonts")
#                 return
#             except Exception as e:
#                 self.log_warn(f"CID font fallback failed: {e}")

#         except Exception as e:
#             self.log_warn(f"Font init failed: {e}")

#     # -----------------------------
#     # Utilities
#     # -----------------------------
#     def _safe_text(self, value, default: str = "확인 필요") -> str:
#         if value is None:
#             return default
#         if isinstance(value, str):
#             v = value.strip()
#             return v if v else default
#         return str(value)

#     def _safe_join(self, items, limit: Optional[int] = None, default: str = "해당 없음") -> str:
#         if not items:
#             return default
#         clean = [self._safe_text(x, "").strip() for x in items if self._safe_text(x, "").strip()]
#         if not clean:
#             return default
#         if limit is not None:
#             clean = clean[:limit]
#         return ", ".join(clean)

#     def _safe_percent(self, value, default: str = "확인 필요") -> str:
#         try:
#             if value is None:
#                 return default
#             return f"{float(value):.1%}"
#         except Exception:
#             return default

#     def _escape(self, text: str) -> str:
#         if text is None:
#             return ""
#         return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

#     def _style(
#         self,
#         name: str,
#         parent,
#         size: int = 10,
#         color=None,
#         bold: bool = False,
#         align: int = TA_LEFT,
#         leading: Optional[int] = None,
#         space_after: int = 6,
#         left_indent: int = 0,
#     ) -> ParagraphStyle:
#         return ParagraphStyle(
#             name=name,
#             parent=parent,
#             fontName=self.pdf_font_name_bold if bold else self.pdf_font_name,
#             fontSize=size,
#             textColor=color or self.color_text,
#             alignment=align,
#             leading=leading or size + 3,
#             spaceAfter=space_after,
#             leftIndent=left_indent,
#         )

#     def _recommendation_text(self, decision) -> str:
#         try:
#             if decision.recommendation:
#                 return decision.recommendation.value.upper()
#         except Exception:
#             pass
#         return self._safe_text(getattr(decision, "recommendation", None), "확인 필요")

#     # -----------------------------
#     # Main
#     # -----------------------------
#     def execute(
#         self,
#         startup: StartupProfile,
#         tech_analysis: TechnologyAnalysisResult,
#         market_analysis: MarketabilityAnalysisResult,
#         impact_analysis: ImpactAnalysisResult,
#         data_moat_analysis: DataMoatAnalysisResult,
#         competitor_analysis: CompetitorAnalysisResult,
#         investment_decision: InvestmentDecision,
#     ) -> FullEvaluationResult:
#         self.start_execution()

#         try:
#             self.log_info(f"Generating report for {startup.name}")

#             evaluation = FullEvaluationResult(
#                 startup=startup,
#                 technology_analysis=tech_analysis,
#                 marketability_analysis=market_analysis,
#                 impact_analysis=impact_analysis,
#                 data_moat_analysis=data_moat_analysis,
#                 competitor_analysis=competitor_analysis,
#                 investment_decision=investment_decision,
#             )

#             evaluation.report_content = self._generate_text_report(evaluation)

#             if REPORTLAB_AVAILABLE:
#                 pdf_path = self._generate_pdf_report(evaluation)
#                 if pdf_path:
#                     self.log_info(f"PDF report generated: {pdf_path}")

#             return evaluation

#         finally:
#             self.end_execution()

#     # -----------------------------
#     # Text report
#     # -----------------------------
#     def _generate_text_report(self, evaluation: FullEvaluationResult) -> str:
#         s = evaluation.startup
#         t = evaluation.technology_analysis
#         m = evaluation.marketability_analysis
#         i = evaluation.impact_analysis
#         d = evaluation.data_moat_analysis
#         c = evaluation.competitor_analysis
#         inv = evaluation.investment_decision

#         lines = []
#         lines.append("=" * 80)
#         lines.append("AgTech Startup Investment Evaluation Report")
#         lines.append("=" * 80)
#         lines.append("")
#         lines.append("[Executive Summary]")
#         lines.append(f"기업명: {self._safe_text(getattr(s, 'name', None))}")
#         lines.append(f"설립연도: {self._safe_text(getattr(s, 'founded_year', None), '미상')}")
#         lines.append(f"단계: {self._safe_text(getattr(s, 'stage', None), '미상')}")
#         lines.append(f"본사: {self._safe_text(getattr(s, 'headquarters', None), '미상')}")
#         lines.append(f"투자 의견: {self._recommendation_text(inv)}")
#         lines.append(f"종합 점수: {self._safe_percent(getattr(inv, 'overall_assessment_score', None))}")
#         lines.append(f"신뢰도: {self._safe_percent(getattr(inv, 'confidence_score', None))}")
#         lines.append(f"핵심 판단: {self._safe_text(getattr(inv, 'rationale', None), '자료 부족')}")
#         lines.append("")
#         lines.append("[Technology]")
#         lines.append(f"핵심 기술: {self._safe_text(getattr(t, 'core_technology', None))}")
#         lines.append(f"Novelty: {self._safe_percent(getattr(t, 'novelty_score', None))}")
#         lines.append(f"Defensibility: {self._safe_percent(getattr(t, 'defensibility_score', None))}")
#         lines.append(f"특허: {self._safe_join(getattr(t, 'patents', None), limit=5)}")
#         lines.append(f"논문: {self._safe_join(getattr(t, 'research_papers', None), limit=5)}")
#         lines.append(f"키워드: {self._safe_join(getattr(t, 'technical_keywords', None), limit=8)}")
#         lines.append("")
#         lines.append("[Investment Decision]")
#         lines.append(f"강점: {self._safe_join(getattr(inv, 'key_strengths', None), limit=5)}")
#         lines.append(f"리스크: {self._safe_join(getattr(inv, 'key_risks', None), limit=5)}")
#         lines.append(f"증거 공백: {self._safe_join(getattr(inv, 'evidence_gaps', None), limit=5)}")
#         lines.append("")
#         lines.append(f"Generated at: {datetime.now().isoformat()}")

#         return "\n".join(lines)

#     # -----------------------------
#     # PDF report
#     # -----------------------------
#     def _generate_pdf_report(self, evaluation: FullEvaluationResult) -> Optional[str]:
#         try:
#             startup_name = self._safe_text(getattr(evaluation.startup, "name", None), "startup")
#             safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in startup_name)
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             pdf_path = os.path.abspath(f"{safe_name}_business_report_{timestamp}.pdf")

#             doc = SimpleDocTemplate(
#                 pdf_path,
#                 pagesize=A4,
#                 rightMargin=1.4 * cm,
#                 leftMargin=1.4 * cm,
#                 topMargin=1.2 * cm,
#                 bottomMargin=1.2 * cm,
#             )

#             styles = getSampleStyleSheet()
#             story = []

#             story.extend(self._build_header_block(evaluation, styles))
#             story.append(Spacer(1, 0.35 * cm))
#             story.extend(self._build_score_cards(evaluation, styles))
#             story.append(Spacer(1, 0.25 * cm))
#             story.extend(self._build_key_message_box(evaluation, styles))
#             story.append(Spacer(1, 0.25 * cm))
#             story.extend(self._build_company_overview(evaluation, styles))
#             story.append(Spacer(1, 0.25 * cm))
#             story.extend(self._build_analysis_summary_table(evaluation, styles))
#             story.append(Spacer(1, 0.25 * cm))

#             story.extend(self._build_section_block(
#                 "Technology Analysis",
#                 [
#                     ("핵심 기술", self._safe_text(getattr(evaluation.technology_analysis, "core_technology", None))),
#                     ("Novelty Score", self._safe_percent(getattr(evaluation.technology_analysis, "novelty_score", None))),
#                     ("Defensibility Score", self._safe_percent(getattr(evaluation.technology_analysis, "defensibility_score", None))),
#                     ("특허", self._safe_join(getattr(evaluation.technology_analysis, "patents", None), limit=5)),
#                     ("논문", self._safe_join(getattr(evaluation.technology_analysis, "research_papers", None), limit=5)),
#                     ("기술 키워드", self._safe_join(getattr(evaluation.technology_analysis, "technical_keywords", None), limit=8)),
#                     ("핵심 해석", self._safe_text(getattr(evaluation.technology_analysis, "summary", None), "자료 부족")),
#                 ],
#                 styles
#             ))

#             story.extend(self._build_section_block(
#                 "Market Analysis",
#                 [
#                     ("Target Market", self._safe_text(getattr(evaluation.marketability_analysis, "target_market_size", None), "미확인")),
#                     ("Growth Potential", self._safe_percent(getattr(evaluation.marketability_analysis, "market_growth_potential", None))),
#                     ("Commercial Feasibility", self._safe_percent(getattr(evaluation.marketability_analysis, "commercial_feasibility_score", None))),
#                     ("Business Model", self._safe_text(getattr(evaluation.marketability_analysis, "business_model", None), "미확인")),
#                     ("Customer Pain Points", self._safe_join(getattr(evaluation.marketability_analysis, "customer_pain_points", None), limit=4)),
#                     ("Adoption Barriers", self._safe_join(getattr(evaluation.marketability_analysis, "adoption_barriers", None), limit=4)),
#                     ("핵심 해석", self._safe_text(getattr(evaluation.marketability_analysis, "summary", None), "자료 부족")),
#                 ],
#                 styles
#             ))

#             story.extend(self._build_section_block(
#                 "Impact Analysis",
#                 [
#                     ("Environmental Impact", self._safe_percent(getattr(evaluation.impact_analysis, "environmental_impact", None))),
#                     ("Agricultural Impact", self._safe_percent(getattr(evaluation.impact_analysis, "agricultural_impact", None))),
#                     ("Sustainability Focus", self._safe_join(getattr(evaluation.impact_analysis, "sustainability_focus", None), limit=5)),
#                     ("Efficiency Improvements", self._safe_join(getattr(evaluation.impact_analysis, "efficiency_improvements", None), limit=5)),
#                     ("Yield Improvement", self._safe_text(getattr(evaluation.impact_analysis, "yield_improvement_claimed", None), "확인 필요")),
#                     ("Carbon Reduction", self._safe_text(getattr(evaluation.impact_analysis, "carbon_reduction_claimed", None), "확인 필요")),
#                     ("핵심 해석", self._safe_text(getattr(evaluation.impact_analysis, "summary", None), "자료 부족")),
#                 ],
#                 styles
#             ))

#             story.extend(self._build_section_block(
#                 "Data Moat Analysis",
#                 [
#                     ("Moat Strength", self._safe_percent(getattr(evaluation.data_moat_analysis, "moat_strength_score", None))),
#                     ("Proprietary Dataset", self._safe_text(getattr(evaluation.data_moat_analysis, "proprietary_dataset_exists", None), "확인 필요")),
#                     ("Dataset Defensibility", self._safe_percent(getattr(evaluation.data_moat_analysis, "dataset_defensibility_score", None))),
#                     ("Flywheel Potential", self._safe_percent(getattr(evaluation.data_moat_analysis, "flywheel_potential_score", None))),
#                     ("Data Sources", self._safe_join(getattr(evaluation.data_moat_analysis, "data_sources", None), limit=5)),
#                     ("핵심 해석", self._safe_text(getattr(evaluation.data_moat_analysis, "summary", None), "자료 부족")),
#                 ],
#                 styles
#             ))

#             story.extend(self._build_section_block(
#                 "Competitive Analysis",
#                 [
#                     ("Competitive Position", self._safe_percent(getattr(evaluation.competitor_analysis, "competitive_advantage_score", None))),
#                     ("Comparable Competitors", self._safe_join(getattr(evaluation.competitor_analysis, "comparable_competitors", None), limit=5)),
#                     ("Technology Differentiation", self._safe_text(getattr(evaluation.competitor_analysis, "technology_differentiation", None), "확인 필요")),
#                     ("Relative Strengths", self._safe_join(getattr(evaluation.competitor_analysis, "relative_strengths", None), limit=4)),
#                     ("Relative Weaknesses", self._safe_join(getattr(evaluation.competitor_analysis, "relative_weaknesses", None), limit=4)),
#                     ("핵심 해석", self._safe_text(getattr(evaluation.competitor_analysis, "summary", None), "자료 부족")),
#                 ],
#                 styles
#             ))

#             story.extend(self._build_risk_strength_gap_boxes(evaluation, styles))
#             story.append(Spacer(1, 0.2 * cm))
#             story.extend(self._build_footer(evaluation, styles))

#             doc.build(story)
#             return pdf_path

#         except Exception as e:
#             self.log_warn(f"PDF generation failed: {e}")
#             return None

#     # -----------------------------
#     # PDF components
#     # -----------------------------
#     def _build_header_block(self, evaluation, styles):
#         startup = evaluation.startup

#         title = self._style("title", styles["Heading1"], size=20, color=self.color_primary, bold=True, align=TA_LEFT, leading=24, space_after=4)
#         subtitle = self._style("subtitle", styles["Normal"], size=9, color=self.color_muted, align=TA_LEFT, leading=12, space_after=2)
#         company = self._style("company", styles["Normal"], size=15, color=black, bold=True, align=TA_LEFT, leading=18, space_after=0)

#         box = Table(
#             [[
#                 Paragraph("AgTech Startup Investment Report", title),
#                 Paragraph(
#                     self._escape(f"{self._safe_text(getattr(startup, 'name', None))}<br/>{self._safe_text(getattr(startup, 'stage', None), '미상')} · {self._safe_text(getattr(startup, 'headquarters', None), '미상')}"),
#                     company,
#                 ),
#                 Paragraph(self._escape("투자 검토용 개괄 보고서"), subtitle),
#             ]],
#             colWidths=[18.2 * cm],
#         )
#         box.setStyle(TableStyle([
#             ("BACKGROUND", (0, 0), (-1, -1), self.color_primary_light),
#             ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
#             ("LEFTPADDING", (0, 0), (-1, -1), 12),
#             ("RIGHTPADDING", (0, 0), (-1, -1), 12),
#             ("TOPPADDING", (0, 0), (-1, -1), 12),
#             ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
#         ]))
#         return [box]

#     def _build_score_cards(self, evaluation, styles):
#         inv = evaluation.investment_decision

#         label = self._style("card_label", styles["Normal"], size=8, color=self.color_muted, align=TA_CENTER, leading=10, space_after=2)
#         value = self._style("card_value", styles["Normal"], size=13, color=black, bold=True, align=TA_CENTER, leading=16, space_after=0)

#         recommendation = self._recommendation_text(inv)
#         overall = self._safe_percent(getattr(inv, "overall_assessment_score", None))
#         confidence = self._safe_percent(getattr(inv, "confidence_score", None))

#         data = [[
#             Paragraph("Recommendation", label),
#             Paragraph("Overall Score", label),
#             Paragraph("Confidence", label),
#         ], [
#             Paragraph(self._escape(recommendation), value),
#             Paragraph(self._escape(overall), value),
#             Paragraph(self._escape(confidence), value),
#         ]]

#         table = Table(data, colWidths=[6.05 * cm, 6.05 * cm, 6.05 * cm])
#         table.setStyle(TableStyle([
#             ("BACKGROUND", (0, 0), (-1, 0), self.color_section_bg),
#             ("BACKGROUND", (0, 1), (-1, 1), white),
#             ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
#             ("GRID", (0, 0), (-1, -1), 0.5, self.color_border),
#             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
#             ("TOPPADDING", (0, 0), (-1, -1), 10),
#             ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
#             ("FONTNAME", (0, 0), (-1, 0), self.pdf_font_name_bold),
#             ("FONTNAME", (0, 1), (-1, 1), self.pdf_font_name_bold),
#         ]))
#         return [table]

#     def _build_key_message_box(self, evaluation, styles):
#         inv = evaluation.investment_decision
#         body = self._style("keymsg", styles["Normal"], size=10, color=self.color_text, leading=14, space_after=0)

#         text = (
#             f"<b>투자 판단 핵심 포인트</b><br/>"
#             f"{self._escape(self._safe_text(getattr(inv, 'rationale', None), '자료 부족'))}"
#         )

#         table = Table([[Paragraph(text, body)]], colWidths=[18.2 * cm])
#         table.setStyle(TableStyle([
#             ("BACKGROUND", (0, 0), (-1, -1), self.color_box_bg),
#             ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
#             ("LEFTPADDING", (0, 0), (-1, -1), 12),
#             ("RIGHTPADDING", (0, 0), (-1, -1), 12),
#             ("TOPPADDING", (0, 0), (-1, -1), 10),
#             ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
#         ]))
#         return [table]

#     def _build_company_overview(self, evaluation, styles):
#         s = evaluation.startup
#         label = self._style("ov_label", styles["Normal"], size=9, color=self.color_muted, bold=True, leading=11)
#         value = self._style("ov_value", styles["Normal"], size=10, color=self.color_text, leading=13)

#         data = [
#             [Paragraph("기업명", label), Paragraph(self._escape(self._safe_text(getattr(s, "name", None))), value),
#              Paragraph("설립연도", label), Paragraph(self._escape(self._safe_text(getattr(s, "founded_year", None), "미상")), value)],
#             [Paragraph("단계", label), Paragraph(self._escape(self._safe_text(getattr(s, "stage", None), "미상")), value),
#              Paragraph("본사", label), Paragraph(self._escape(self._safe_text(getattr(s, "headquarters", None), "미상")), value)],
#         ]

#         table = Table(data, colWidths=[2.3 * cm, 6.8 * cm, 2.3 * cm, 6.8 * cm])
#         table.setStyle(TableStyle([
#             ("BACKGROUND", (0, 0), (-1, -1), white),
#             ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
#             ("GRID", (0, 0), (-1, -1), 0.5, self.color_border),
#             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
#             ("TOPPADDING", (0, 0), (-1, -1), 8),
#             ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
#             ("BACKGROUND", (0, 0), (0, -1), self.color_section_bg),
#             ("BACKGROUND", (2, 0), (2, -1), self.color_section_bg),
#         ]))
#         return [table]

#     def _build_analysis_summary_table(self, evaluation, styles):
#         t = evaluation.technology_analysis
#         m = evaluation.marketability_analysis
#         i = evaluation.impact_analysis
#         d = evaluation.data_moat_analysis
#         c = evaluation.competitor_analysis

#         header = self._style("summary_header", styles["Normal"], size=8, color=self.color_muted, bold=True, align=TA_CENTER)
#         value = self._style("summary_value", styles["Normal"], size=11, color=black, bold=True, align=TA_CENTER)

#         data = [
#             [
#                 Paragraph("Technology", header),
#                 Paragraph("Market", header),
#                 Paragraph("Impact", header),
#                 Paragraph("Data Moat", header),
#                 Paragraph("Competitive", header),
#             ],
#             [
#                 Paragraph(self._escape(self._safe_percent(getattr(t, "novelty_score", None))), value),
#                 Paragraph(self._escape(self._safe_percent(getattr(m, "commercial_feasibility_score", None))), value),
#                 Paragraph(self._escape(self._safe_percent(getattr(i, "environmental_impact", None))), value),
#                 Paragraph(self._escape(self._safe_percent(getattr(d, "moat_strength_score", None))), value),
#                 Paragraph(self._escape(self._safe_percent(getattr(c, "competitive_advantage_score", None))), value),
#             ]
#         ]

#         table = Table(data, colWidths=[3.64 * cm] * 5)
#         table.setStyle(TableStyle([
#             ("BACKGROUND", (0, 0), (-1, 0), self.color_section_bg),
#             ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
#             ("GRID", (0, 0), (-1, -1), 0.5, self.color_border),
#             ("TOPPADDING", (0, 0), (-1, -1), 8),
#             ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
#         ]))
#         return [table]

#     def _build_section_block(self, title: str, rows: List[tuple], styles):
#         title_style = self._style(
#             f"title_{title}",
#             styles["Heading2"],
#             size=12,
#             color=self.color_primary,
#             bold=True,
#             leading=15,
#             space_after=4,
#         )
#         label = self._style(f"label_{title}", styles["Normal"], size=8, color=self.color_muted, bold=True, leading=10)
#         value = self._style(f"value_{title}", styles["Normal"], size=9, color=self.color_text, leading=12)

#         title_bar = Table([[Paragraph(self._escape(title), title_style)]], colWidths=[18.2 * cm])
#         title_bar.setStyle(TableStyle([
#             ("BACKGROUND", (0, 0), (-1, -1), self.color_section_bg),
#             ("BOX", (0, 0), (-1, -1), 0.6, self.color_border),
#             ("LEFTPADDING", (0, 0), (-1, -1), 10),
#             ("RIGHTPADDING", (0, 0), (-1, -1), 10),
#             ("TOPPADDING", (0, 0), (-1, -1), 7),
#             ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
#         ]))

#         table_rows = []
#         for k, v in rows:
#             table_rows.append([
#                 Paragraph(self._escape(k), label),
#                 Paragraph(self._escape(v), value),
#             ])

#         detail_table = Table(table_rows, colWidths=[4.0 * cm, 14.2 * cm])
#         detail_table.setStyle(TableStyle([
#             ("BOX", (0, 0), (-1, -1), 0.6, self.color_border),
#             ("GRID", (0, 0), (-1, -1), 0.4, self.color_border),
#             ("BACKGROUND", (0, 0), (0, -1), HexColor("#FAFBFD")),
#             ("VALIGN", (0, 0), (-1, -1), "TOP"),
#             ("TOPPADDING", (0, 0), (-1, -1), 6),
#             ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
#             ("LEFTPADDING", (0, 0), (-1, -1), 8),
#             ("RIGHTPADDING", (0, 0), (-1, -1), 8),
#         ]))

#         return [Spacer(1, 0.18 * cm), KeepTogether([title_bar, Spacer(1, 0.08 * cm), detail_table])]

#     def _build_risk_strength_gap_boxes(self, evaluation, styles):
#         inv = evaluation.investment_decision

#         title = self._style("rsg_title", styles["Normal"], size=9, color=black, bold=True, leading=12)
#         body = self._style("rsg_body", styles["Normal"], size=9, color=self.color_text, leading=12)

#         strengths = Paragraph(
#             f"<b>Key Strengths</b><br/>{self._escape(self._safe_join(getattr(inv, 'key_strengths', None), limit=5))}",
#             body,
#         )
#         risks = Paragraph(
#             f"<b>Key Risks</b><br/>{self._escape(self._safe_join(getattr(inv, 'key_risks', None), limit=5))}",
#             body,
#         )
#         gaps = Paragraph(
#             f"<b>Evidence Gaps</b><br/>{self._escape(self._safe_join(getattr(inv, 'evidence_gaps', None), limit=5))}",
#             body,
#         )

#         table = Table([[strengths, risks, gaps]], colWidths=[6.05 * cm, 6.05 * cm, 6.05 * cm])
#         table.setStyle(TableStyle([
#             ("BACKGROUND", (0, 0), (0, 0), HexColor("#F2FBF5")),
#             ("BACKGROUND", (1, 0), (1, 0), HexColor("#FFF6F5")),
#             ("BACKGROUND", (2, 0), (2, 0), HexColor("#F8F8FA")),
#             ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
#             ("GRID", (0, 0), (-1, -1), 0.5, self.color_border),
#             ("VALIGN", (0, 0), (-1, -1), "TOP"),
#             ("LEFTPADDING", (0, 0), (-1, -1), 10),
#             ("RIGHTPADDING", (0, 0), (-1, -1), 10),
#             ("TOPPADDING", (0, 0), (-1, -1), 10),
#             ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
#         ]))
#         return [table]

#     def _build_footer(self, evaluation, styles):
#         footer = self._style("footer", styles["Normal"], size=8, color=self.color_muted, align=TA_CENTER, leading=10, space_after=0)
#         ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         return [Paragraph(self._escape(f"Report Generated: {ts}"), footer)]

#     # -----------------------------
#     # Save text report
#     # -----------------------------
#     def save_report(self, evaluation: FullEvaluationResult, filepath: str) -> bool:
#         try:
#             with open(filepath, "w", encoding="utf-8") as f:
#                 f.write(self._safe_text(getattr(evaluation, "report_content", None), ""))
#             self.log_info(f"Report saved to {filepath}")
#             return True
#         except Exception as e:
#             self.log_warn(f"Failed to save report: {e}")
#             return False

"""Report Generation Agent - 한국어 중심의 PDF 투자평가 보고서 생성."""

import os
import sys
from datetime import datetime
from typing import Optional, List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, black, white
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
        self.pdf_font_name = "Helvetica"
        self.pdf_font_name_bold = "Helvetica-Bold"
        self._init_fonts()

        self.color_primary = HexColor("#17365D")
        self.color_primary_light = HexColor("#EAF2FF")
        self.color_border = HexColor("#D7DDE5")
        self.color_text = HexColor("#222222")
        self.color_muted = HexColor("#666666")
        self.color_box_bg = HexColor("#F7F9FC")
        self.color_section_bg = HexColor("#F3F6FA")

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
                    "INVEST": "투자 검토",
                    "PASS": "보류",
                    "HOLD": "추가 검토",
                    "REJECT": "투자 비추천",
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

            evaluation.report_content = self._generate_text_report(evaluation)

            if REPORTLAB_AVAILABLE:
                pdf_path = self._generate_pdf_report(evaluation)
                if pdf_path:
                    self.log_info(f"PDF report generated: {pdf_path}")

            return evaluation

        finally:
            self.end_execution()

    # -----------------------------
    # 텍스트 보고서
    # -----------------------------
    def _generate_text_report(self, evaluation: FullEvaluationResult) -> str:
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
                    ("성장 가능성", self._safe_percent(getattr(evaluation.marketability_analysis, "market_growth_potential", None))),
                    ("사업화 가능성", self._safe_percent(getattr(evaluation.marketability_analysis, "commercial_feasibility_score", None))),
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
            story.append(Spacer(1, 0.2 * cm))
            story.extend(self._build_footer(evaluation, styles))

            doc.build(story)
            return pdf_path

        except Exception as e:
            self.log_warn(f"PDF generation failed: {e}")
            return None

    # -----------------------------
    # PDF 구성요소
    # -----------------------------
    def _build_header_block(self, evaluation, styles):
        startup = evaluation.startup

        title = self._style("title", styles["Heading1"], size=20, color=self.color_primary, bold=True, align=TA_LEFT, leading=24, space_after=4)
        subtitle = self._style("subtitle", styles["Normal"], size=9, color=self.color_muted, align=TA_LEFT, leading=12, space_after=2)
        company = self._style("company", styles["Normal"], size=15, color=black, bold=True, align=TA_LEFT, leading=18, space_after=0)

        box = Table(
            [[
                Paragraph("애그테크 스타트업 투자 평가 보고서", title),
                Paragraph(
                    self._escape(f"{self._safe_text(getattr(startup, 'name', None))}<br/>{self._safe_text(getattr(startup, 'stage', None), '미상')} · {self._safe_text(getattr(startup, 'headquarters', None), '미상')}"),
                    company,
                ),
                Paragraph(self._escape("기존 분석 결과를 종합한 투자 검토용 개괄 보고서"), subtitle),
            ]],
            colWidths=[18.2 * cm],
        )
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.color_primary_light),
            ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        return [box]

    def _build_score_cards(self, evaluation, styles):
        inv = evaluation.investment_decision

        label = self._style("card_label", styles["Normal"], size=8, color=self.color_muted, align=TA_CENTER, leading=10, space_after=2)
        value = self._style("card_value", styles["Normal"], size=13, color=black, bold=True, align=TA_CENTER, leading=16, space_after=0)

        recommendation = self._recommendation_text(inv)
        overall = self._safe_percent(getattr(inv, "overall_assessment_score", None))
        confidence = self._safe_percent(getattr(inv, "confidence_score", None))

        data = [[
            Paragraph("투자 의견", label),
            Paragraph("종합 점수", label),
            Paragraph("판단 신뢰도", label),
        ], [
            Paragraph(self._escape(recommendation), value),
            Paragraph(self._escape(overall), value),
            Paragraph(self._escape(confidence), value),
        ]]

        table = Table(data, colWidths=[6.05 * cm, 6.05 * cm, 6.05 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.color_section_bg),
            ("BACKGROUND", (0, 1), (-1, 1), white),
            ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
            ("GRID", (0, 0), (-1, -1), 0.5, self.color_border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (-1, 0), self.pdf_font_name_bold),
            ("FONTNAME", (0, 1), (-1, 1), self.pdf_font_name_bold),
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
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#FDEEEE")),
            ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
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
            ("BACKGROUND", (0, 0), (-1, -1), white),
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
        t = evaluation.technology_analysis
        m = evaluation.marketability_analysis
        i = evaluation.impact_analysis
        d = evaluation.data_moat_analysis
        c = evaluation.competitor_analysis

        header = self._style("summary_header", styles["Normal"], size=8, color=self.color_muted, bold=True, align=TA_CENTER)
        value = self._style("summary_value", styles["Normal"], size=11, color=black, bold=True, align=TA_CENTER)

        data = [
            [
                Paragraph("기술", header),
                Paragraph("시장성", header),
                Paragraph("임팩트", header),
                Paragraph("데이터 해자", header),
                Paragraph("경쟁력", header),
            ],
            [
                Paragraph(self._escape(self._safe_percent(getattr(t, "novelty_score", None))), value),
                Paragraph(self._escape(self._safe_percent(getattr(m, "commercial_feasibility_score", None))), value),
                Paragraph(self._escape(self._safe_percent(getattr(i, "environmental_impact", None))), value),
                Paragraph(self._escape(self._safe_percent(getattr(d, "moat_strength_score", None))), value),
                Paragraph(self._escape(self._safe_percent(getattr(c, "competitive_advantage_score", None))), value),
            ]
        ]

        table = Table(data, colWidths=[3.64 * cm] * 5)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.color_section_bg),
            ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
            ("GRID", (0, 0), (-1, -1), 0.5, self.color_border),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        return [table]

    def _build_section_block(self, title: str, rows: List[tuple], styles):
        title_style = self._style(
            f"title_{title}",
            styles["Heading2"],
            size=12,
            color=self.color_primary,
            bold=True,
            leading=15,
            space_after=4,
        )
        label = self._style(f"label_{title}", styles["Normal"], size=8, color=self.color_muted, bold=True, leading=10)
        value = self._style(f"value_{title}", styles["Normal"], size=9, color=self.color_text, leading=12)

        title_bar = Table([[Paragraph(self._escape(title), title_style)]], colWidths=[18.2 * cm])
        title_bar.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.color_section_bg),
            ("BOX", (0, 0), (-1, -1), 0.6, self.color_border),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
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
            ("BOX", (0, 0), (-1, -1), 0.6, self.color_border),
            ("GRID", (0, 0), (-1, -1), 0.4, self.color_border),
            ("BACKGROUND", (0, 0), (0, -1), HexColor("#FAFBFD")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))

        return [Spacer(1, 0.18 * cm), KeepTogether([title_bar, Spacer(1, 0.08 * cm), detail_table])]

    def _build_risk_strength_gap_boxes(self, evaluation, styles):
        inv = evaluation.investment_decision
        body = self._style("rsg_body", styles["Normal"], size=9, color=self.color_text, leading=12)

        strengths = Paragraph(
            f"<b>주요 강점</b><br/>{self._escape(self._safe_join(getattr(inv, 'key_strengths', None), limit=5))}",
            body,
        )
        risks = Paragraph(
            f"<b>주요 리스크</b><br/>{self._escape(self._safe_join(getattr(inv, 'key_risks', None), limit=5))}",
            body,
        )
        gaps = Paragraph(
            f"<b>증거 공백</b><br/>{self._escape(self._safe_join(getattr(inv, 'evidence_gaps', None), limit=5))}",
            body,
        )

        table = Table([[strengths, risks, gaps]], colWidths=[6.05 * cm, 6.05 * cm, 6.05 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), HexColor("#F2FBF5")),
            ("BACKGROUND", (1, 0), (1, 0), HexColor("#FFF6F5")),
            ("BACKGROUND", (2, 0), (2, 0), HexColor("#F8F8FA")),
            ("BOX", (0, 0), (-1, -1), 0.8, self.color_border),
            ("GRID", (0, 0), (-1, -1), 0.5, self.color_border),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        return [table]

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