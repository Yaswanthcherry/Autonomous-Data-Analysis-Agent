"""
PDF report generation using ReportLab
"""
import os
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from loguru import logger


class PDFService:
    def generate(
        self,
        job_id: str,
        profile: dict,
        cleaning: dict,
        eda: dict,
        model_results: list[dict],
        findings: str,
        feature_recs: str,
        insights: str,
        summary: str,
        output_dir: str = "/app/uploads",
    ) -> str:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"report_{job_id}.pdf"
        filepath = os.path.join(output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)

        styles = getSampleStyleSheet()
        h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=20,
                             textColor=colors.HexColor("#1a1a2e"), spaceAfter=12)
        h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=14,
                             textColor=colors.HexColor("#16213e"), spaceAfter=8)
        body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10,
                               leading=14, spaceAfter=6)
        caption = ParagraphStyle("caption", parent=styles["Normal"], fontSize=8,
                                  textColor=colors.grey)

        story = []

        # ── Title ──
        story.append(Paragraph("AI Data Analysis Report", h1))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Job: {job_id[:8]}", caption))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0")))
        story.append(Spacer(1, 0.2*inch))

        # ── Executive Summary ──
        story.append(Paragraph("Executive Summary", h2))
        story.append(Paragraph(summary.replace("\n", "<br/>"), body))
        story.append(Spacer(1, 0.15*inch))

        # ── Dataset Profile ──
        story.append(Paragraph("Dataset Profile", h2))
        shape = profile.get("shape", {})
        profile_data = [
            ["Metric", "Value"],
            ["Total Rows", str(shape.get("rows", "N/A"))],
            ["Total Columns", str(shape.get("cols", "N/A"))],
            ["Memory Usage", f"{profile.get('memory_mb', 'N/A')} MB"],
            ["Duplicate Rows", str(profile.get("duplicate_rows", 0))],
            ["Task Type", eda.get("task_type", "N/A")],
            ["Target Column", str(eda.get("target_candidate", "N/A"))],
        ]
        story.append(self._make_table(profile_data))
        story.append(Spacer(1, 0.15*inch))

        # ── Key Findings ──
        story.append(Paragraph("Key Findings", h2))
        story.append(Paragraph(findings.replace("\n", "<br/>"), body))
        story.append(Spacer(1, 0.15*inch))

        # ── Feature Recommendations ──
        story.append(Paragraph("Feature Recommendations", h2))
        story.append(Paragraph(feature_recs.replace("\n", "<br/>"), body))
        story.append(Spacer(1, 0.15*inch))

        # ── Model Comparison ──
        story.append(Paragraph("Model Performance Comparison", h2))
        if model_results:
            task = model_results[0].get("task_type", "classification")
            if task == "classification":
                headers = ["Model", "Accuracy", "F1 Score", "ROC-AUC", "Best"]
                rows = [headers] + [
                    [
                        m["model_name"],
                        str(m["metrics"].get("accuracy", "N/A")),
                        str(m["metrics"].get("f1", "N/A")),
                        str(m["metrics"].get("roc_auc", "N/A")),
                        "✓" if m.get("is_best") else "",
                    ]
                    for m in model_results
                ]
            else:
                headers = ["Model", "RMSE", "MAE", "R²", "Best"]
                rows = [headers] + [
                    [
                        m["model_name"],
                        str(m["metrics"].get("rmse", "N/A")),
                        str(m["metrics"].get("mae", "N/A")),
                        str(m["metrics"].get("r2", "N/A")),
                        "✓" if m.get("is_best") else "",
                    ]
                    for m in model_results
                ]
            story.append(self._make_table(rows))
        story.append(Spacer(1, 0.15*inch))

        # ── Business Insights ──
        story.append(Paragraph("Business Insights", h2))
        story.append(Paragraph(insights.replace("\n", "<br/>"), body))

        doc.build(story)
        logger.info(f"PDF report generated: {filepath}")
        return filepath

    def _make_table(self, data: list) -> Table:
        t = Table(data, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        return t
