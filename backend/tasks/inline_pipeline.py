"""
Inline async pipeline — runs directly as a FastAPI BackgroundTask.
No Celery or Redis required. Full 13-stage pipeline.
"""
import uuid
import asyncio
from datetime import datetime, timezone
import pandas as pd
from loguru import logger

from core.database import AsyncSessionLocal
from core.config import settings
from services.data_profiler import DataProfiler
from services.data_cleaner import DataCleaner
from services.anomaly_detector import AnomalyDetector
from services.eda_service import EDAService
from services.chart_service import ChartService
from services.ml_service import MLService
from services.ai_service import AIService
from services.pdf_service import PDFService


async def _update_job(db, job_id: str, **kwargs):
    from sqlalchemy import select
    from models.analysis import AnalysisJob
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = result.scalar_one_or_none()
    if job:
        for k, v in kwargs.items():
            setattr(job, k, v)
        await db.commit()


async def _save_result(db, job_id: str, result_type: str, data: dict):
    from models.analysis import AnalysisResult
    r = AnalysisResult(id=str(uuid.uuid4()), job_id=job_id, result_type=result_type, data=data)
    db.add(r)
    await db.commit()


async def _save_charts(db, job_id: str, charts: list):
    from models.analysis import Chart
    for c in charts:
        db.add(Chart(
            id=str(uuid.uuid4()), job_id=job_id,
            title=c["title"], chart_type=c["chart_type"], plotly_json=c["plotly_json"]
        ))
    await db.commit()


async def _save_models(db, job_id: str, model_results: list):
    from models.analysis import MLModel
    for m in model_results:
        db.add(MLModel(
            id=str(uuid.uuid4()), job_id=job_id,
            model_name=m["model_name"], task_type=m["task_type"],
            metrics=m["metrics"], feature_importance=m.get("feature_importance", {}),
            is_best=m.get("is_best", False)
        ))
    await db.commit()


async def _save_report(db, job_id: str, pdf_path: str, summary: str, insights: str):
    from models.analysis import Report
    db.add(Report(
        id=str(uuid.uuid4()), job_id=job_id,
        pdf_path=pdf_path, executive_summary=summary, business_insights=insights
    ))
    await db.commit()


async def run_pipeline_inline(job_id: str, dataset_id: str, file_path: str, file_type: str):
    """Full 13-stage async analysis pipeline."""
    async with AsyncSessionLocal() as db:
        try:
            await _update_job(db, job_id, status="running",
                              started_at=datetime.now(timezone.utc),
                              current_stage="loading", progress=5)

            # ── Load ─────────────────────────────────────────────────
            logger.info(f"[{job_id[:8]}] Loading {file_type}: {file_path}")
            loop = asyncio.get_event_loop()
            if file_type == "csv":
                df = await loop.run_in_executor(None, pd.read_csv, file_path)
            elif file_type == "xlsx":
                df = await loop.run_in_executor(None, pd.read_excel, file_path)
            else:
                df = await loop.run_in_executor(None, pd.read_json, file_path)
            logger.info(f"[{job_id[:8]}] Shape: {df.shape}")

            # ── Stage 1: Profile ──────────────────────────────────────
            await _update_job(db, job_id, current_stage="profiling", progress=8)
            profile = await loop.run_in_executor(None, DataProfiler().profile, df)
            await _save_result(db, job_id, "profile", profile)

            # Update dataset counts
            from sqlalchemy import select
            from models.dataset import Dataset
            ds_result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
            ds = ds_result.scalar_one_or_none()
            if ds:
                ds.row_count = profile["shape"]["rows"]
                ds.col_count = profile["shape"]["cols"]
                ds.status = "analyzing"
                await db.commit()

            # ── Stage 2: Clean ────────────────────────────────────────
            await _update_job(db, job_id, current_stage="cleaning", progress=16)
            cleaner = DataCleaner()
            df_clean, cleaning_report = await loop.run_in_executor(
                None, cleaner.clean, df.copy()
            )
            await _save_result(db, job_id, "cleaning", cleaning_report)

            # ── Stage 3: Anomaly Detection ────────────────────────────
            await _update_job(db, job_id, current_stage="anomaly_detection", progress=24)
            anomalies = await loop.run_in_executor(None, AnomalyDetector().detect, df_clean)
            await _save_result(db, job_id, "anomalies", anomalies)

            # ── Stage 4: EDA ──────────────────────────────────────────
            await _update_job(db, job_id, current_stage="eda", progress=32)
            eda = await loop.run_in_executor(None, EDAService().analyze, df_clean)
            await _save_result(db, job_id, "eda", eda)

            # ── Stage 5: Charts ───────────────────────────────────────
            await _update_job(db, job_id, current_stage="chart_generation", progress=42)
            charts = await loop.run_in_executor(
                None, ChartService().generate_all, df_clean, eda
            )
            await _save_charts(db, job_id, charts)

            # ── Stage 6: AI Findings ──────────────────────────────────
            await _update_job(db, job_id, current_stage="ai_findings", progress=52)
            ai = AIService()
            findings = await ai.explain_findings(profile, cleaning_report, anomalies)
            await _save_result(db, job_id, "findings", {"text": findings})

            # ── Stage 7: Feature Recommendations ─────────────────────
            await _update_job(db, job_id, current_stage="feature_recommendations", progress=60)
            feature_recs = await ai.recommend_features(eda, profile)
            await _save_result(db, job_id, "feature_recommendations", {"text": feature_recs})

            # ── Stage 8 & 9: ML Training & Comparison ────────────────
            await _update_job(db, job_id, current_stage="model_training", progress=68)
            target = eda.get("target_candidate")
            task_type = eda.get("task_type", "classification")
            model_results = []
            if target and target in df_clean.columns:
                ml_svc = MLService()
                model_results = await loop.run_in_executor(
                    None, ml_svc.train, df_clean, task_type, target
                )
                await _save_models(db, job_id, model_results)
            await _update_job(db, job_id, current_stage="model_comparison", progress=76)

            # ── Stage 10: Business Insights ───────────────────────────
            await _update_job(db, job_id, current_stage="business_insights", progress=82)
            insights = await ai.generate_business_insights(eda, model_results)

            # ── Stage 11: Executive Summary ───────────────────────────
            await _update_job(db, job_id, current_stage="executive_summary", progress=88)
            summary = await ai.generate_executive_summary(
                profile, eda, model_results, findings, insights
            )

            # ── Stage 12: PDF Export ──────────────────────────────────
            await _update_job(db, job_id, current_stage="pdf_export", progress=94)
            import os
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            pdf_svc = PDFService()
            pdf_path = await loop.run_in_executor(
                None,
                lambda: pdf_svc.generate(
                    job_id=job_id, profile=profile, cleaning=cleaning_report,
                    eda=eda, model_results=model_results, findings=findings,
                    feature_recs=feature_recs, insights=insights, summary=summary,
                    output_dir=settings.UPLOAD_DIR,
                )
            )
            await _save_report(db, job_id, pdf_path, summary, insights)

            # ── Complete ──────────────────────────────────────────────
            await _update_job(db, job_id, status="completed", current_stage="complete",
                              progress=100, completed_at=datetime.now(timezone.utc))
            if ds:
                ds.status = "analyzed"
                await db.commit()

            logger.info(f"[{job_id[:8]}] ✓ Pipeline completed")

        except Exception as exc:
            logger.error(f"[{job_id[:8]}] Pipeline failed: {exc}")
            try:
                await _update_job(db, job_id, status="failed", error_message=str(exc)[:500])
            except Exception:
                pass
