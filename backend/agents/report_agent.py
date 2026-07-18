"""
ReportAgent — PDF report generation.

Responsibilities (Single Responsibility: reporting only):
- Compile all analysis results into a structured PDF
- Include charts, tables, and insights
- Generate executive summary
- Save PDF to output directory

Uses ReportLab for PDF generation.
"""
from __future__ import annotations

from loguru import logger

from agents.schemas import ReportInput, ReportOutput
from services.pdf_service import PDFService


class ReportAgent:
    """
    Wraps PDFService to produce typed ReportOutput.
    Maintains single responsibility while providing agent interface.
    """

    def generate(self, profile: dict, cleaning: dict, eda: dict, model_results: list,
                 findings: str, feature_recs: str, insights: str, summary: str,
                 input_: ReportInput) -> ReportOutput:
        logger.info(f"[{input_.job_id[:8]}] ReportAgent generating PDF")

        # Use existing service for core logic
        pdf_service = PDFService()
        pdf_path = pdf_service.generate(
            job_id=input_.job_id,
            profile=profile,
            cleaning=cleaning,
            eda=eda,
            model_results=model_results,
            findings=findings,
            feature_recs=feature_recs,
            insights=insights,
            summary=summary,
            output_dir=input_.output_dir,
        )

        output = ReportOutput(
            job_id=input_.job_id,
            pdf_path=pdf_path,
            page_count=1,  # PDFService doesn't return page count, default to 1
        )

        logger.info(f"[{input_.job_id[:8]}] PDF generated: {pdf_path}")
        return output
