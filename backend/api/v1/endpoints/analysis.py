from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.dataset import Dataset
from models.analysis import AnalysisJob, AnalysisResult, Chart, MLModel
from tasks.inline_pipeline import run_pipeline_inline
import uuid

router = APIRouter()


@router.post("/{dataset_id}/start", status_code=202)
async def start_analysis(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    job = AnalysisJob(
        id=str(uuid.uuid4()),
        dataset_id=dataset_id,
        status="pending",
        progress=0,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Run pipeline as FastAPI background task (no Celery/Redis needed)
    background_tasks.add_task(
        run_pipeline_inline,
        job.id, dataset_id, dataset.file_path, dataset.file_type
    )

    return {"job_id": job.id, "status": "pending"}


@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "status": job.status,
        "current_stage": job.current_stage,
        "progress": job.progress,
        "error_message": job.error_message,
    }


@router.get("/{job_id}/results")
async def get_results(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.job_id == job_id)
    )
    results = result.scalars().all()
    return [{"type": r.result_type, "data": r.data} for r in results]


@router.get("/{job_id}/charts")
async def get_charts(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Chart).where(Chart.job_id == job_id))
    charts = result.scalars().all()
    return [{"id": c.id, "title": c.title, "chart_type": c.chart_type,
             "plotly_json": c.plotly_json} for c in charts]


@router.get("/{job_id}/models")
async def get_models(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(MLModel).where(MLModel.job_id == job_id))
    models_list = result.scalars().all()
    return [{"id": m.id, "model_name": m.model_name, "task_type": m.task_type,
             "metrics": m.metrics, "is_best": m.is_best,
             "feature_importance": m.feature_importance} for m in models_list]
