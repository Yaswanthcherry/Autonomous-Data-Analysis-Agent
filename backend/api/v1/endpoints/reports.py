from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.analysis import AnalysisJob, Report
import os

router = APIRouter()


@router.get("/{job_id}")
async def get_report(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Report).where(Report.job_id == job_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "executive_summary": report.executive_summary,
        "business_insights": report.business_insights,
        "pdf_available": bool(report.pdf_path and os.path.exists(report.pdf_path)),
        "created_at": report.created_at,
    }


@router.get("/{job_id}/download")
async def download_report(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Report).where(Report.job_id == job_id))
    report = result.scalar_one_or_none()
    if not report or not report.pdf_path or not os.path.exists(report.pdf_path):
        raise HTTPException(status_code=404, detail="PDF report not available")
    return FileResponse(
        report.pdf_path,
        media_type="application/pdf",
        filename=f"analysis_report_{job_id}.pdf",
    )
