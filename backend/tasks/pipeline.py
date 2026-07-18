"""
Main analysis pipeline Celery task — orchestrates all 13 stages using agent-based architecture
"""
import asyncio
import uuid
from datetime import datetime, timezone
import pandas as pd
from loguru import logger

from tasks.celery_app import celery_app
from core.config import settings
from services.anomaly_detector import AnomalyDetector
from agents.planner_agent import PlannerAgent
from agents.profiler_agent import ProfilerAgent
from agents.cleaner_agent import CleanerAgent
from agents.eda_agent import EDAAgent
from agents.visualization_agent import VisualizationAgent
from agents.ml_agent import MLAgent
from agents.insight_agent import InsightAgent
from agents.report_agent import ReportAgent
from agents.schemas import (
    PlannerInput,
    ProfilerInput,
    CleanerInput,
    EDAInput,
    VisualizationInput,
    MLInput,
    InsightInput,
    ReportInput,
)


def _make_sync_session():
    """Create a synchronous SQLAlchemy session for Celery workers."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url, pool_pre_ping=True, pool_size=5)
    Session = sessionmaker(bind=engine)
    return Session()


def _update_job(db, job_id: str, **kwargs):
    from models.analysis import AnalysisJob
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if job:
        for k, v in kwargs.items():
            setattr(job, k, v)
        db.commit()
        db.refresh(job)


def _save_result(db, job_id: str, result_type: str, data: dict):
    from models.analysis import AnalysisResult
    record = AnalysisResult(
        id=str(uuid.uuid4()),
        job_id=job_id,
        result_type=result_type,
        data=data,
    )
    db.add(record)
    db.commit()


def _save_charts(db, job_id: str, charts: list):
    from models.analysis import Chart
    for c in charts:
        chart = Chart(
            id=str(uuid.uuid4()),
            job_id=job_id,
            title=c["title"],
            chart_type=c["chart_type"],
            plotly_json=c["plotly_json"],
        )
        db.add(chart)
    db.commit()


def _save_models(db, job_id: str, model_results: list):
    from models.analysis import MLModel
    for m in model_results:
        ml = MLModel(
            id=str(uuid.uuid4()),
            job_id=job_id,
            model_name=m["model_name"],
            task_type=m["task_type"],
            metrics=m["metrics"],
            feature_importance=m.get("feature_importance", {}),
            is_best=m.get("is_best", False),
        )
        db.add(ml)
    db.commit()


def _save_report(db, job_id: str, pdf_path: str, summary: str, insights: str):
    from models.analysis import Report
    report = Report(
        id=str(uuid.uuid4()),
        job_id=job_id,
        pdf_path=pdf_path,
        executive_summary=summary,
        business_insights=insights,
    )
    db.add(report)
    db.commit()


def _run_async(coro):
    """Run an async coroutine from a sync context safely."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@celery_app.task(bind=True, name="tasks.pipeline.run_analysis_pipeline", max_retries=0)
def run_analysis_pipeline(self, job_id: str, dataset_id: str, file_path: str, file_type: str):
    db = _make_sync_session()
    try:
        _update_job(db, job_id,
                    status="running",
                    started_at=datetime.now(timezone.utc),
                    current_stage="loading",
                    progress=5)

        # ── Load Dataset ─────────────────────────────────────────────
        logger.info(f"[{job_id[:8]}] Loading {file_type} file: {file_path}")
        if file_type == "csv":
            df = pd.read_csv(file_path)
        elif file_type == "xlsx":
            df = pd.read_excel(file_path)
        elif file_type == "json":
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        logger.info(f"[{job_id[:8]}] Loaded dataset shape: {df.shape}")

        # ── Stage 0: Planning (Autonomous orchestration) ─────────────
        _update_job(db, job_id, current_stage="planning", progress=5)
        planner = PlannerAgent()
        planner_input = PlannerInput(
            file_path=file_path,
            file_type=file_type,
            job_id=job_id
        )
        plan = planner.plan(df, planner_input)
        _save_result(db, job_id, "planner", plan.model_dump())
        logger.info(f"[{job_id[:8]}] Plan: {plan.task_type}, target={plan.target_column}, steps={len(plan.recommended_steps)}")

        # ── Stage 1: Profile ─────────────────────────────────────────
        _update_job(db, job_id, current_stage="profiling", progress=10)
        profiler = ProfilerAgent()
        profiler_input = ProfilerInput(job_id=job_id)
        profile_output = profiler.profile(df, profiler_input)
        profile = profile_output.model_dump()
        _save_result(db, job_id, "profile", profile)

        # Update dataset row/col counts
        from models.dataset import Dataset
        ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if ds:
            ds.row_count = profile["rows"]
            ds.col_count = profile["cols"]
            ds.status = "analyzing"
            db.commit()

        # ── Stage 2: Clean ───────────────────────────────────────────
        _update_job(db, job_id, current_stage="cleaning", progress=18)
        cleaner = CleanerAgent()
        cleaner_input = CleanerInput(job_id=job_id, original_shape=[profile["rows"], profile["cols"]])
        df_clean, cleaner_output = cleaner.clean(df.copy(), cleaner_input)
        cleaning_report = cleaner_output.model_dump()
        _save_result(db, job_id, "cleaning", cleaning_report)

        # ── Stage 3: Anomaly Detection ───────────────────────────────
        _update_job(db, job_id, current_stage="anomaly_detection", progress=26)
        anomalies = AnomalyDetector().detect(df_clean)
        _save_result(db, job_id, "anomalies", anomalies)

        # ── Stage 4: EDA ─────────────────────────────────────────────
        _update_job(db, job_id, current_stage="eda", progress=34)
        eda_agent = EDAAgent()
        eda_input = EDAInput(job_id=job_id, target_column=plan.target_column)
        eda_output = eda_agent.analyze(df_clean, eda_input)
        eda = eda_output.model_dump()
        # Override with planner's task type and target for consistency
        eda["task_type"] = plan.task_type
        eda["target_candidate"] = plan.target_column
        _save_result(db, job_id, "eda", eda)

        # ── Stage 5: Charts ──────────────────────────────────────────
        _update_job(db, job_id, current_stage="chart_generation", progress=44)
        viz_agent = VisualizationAgent()
        viz_input = VisualizationInput(job_id=job_id, task_type=plan.task_type, target_column=plan.target_column or "")
        viz_output = viz_agent.generate(df_clean, eda, viz_input)
        charts = [c.model_dump() for c in viz_output.charts]
        _save_charts(db, job_id, charts)

        # ── Stage 6-11: Insights (combined for efficiency) ─────────────
        _update_job(db, job_id, current_stage="ai_insights", progress=54)
        insight_agent = InsightAgent()
        insight_input = InsightInput(
            job_id=job_id,
            task_type=plan.task_type,
            target_column=plan.target_column or "",
        )
        insight_output = insight_agent.generate(profile, cleaning_report, anomalies, eda, [], insight_input)
        insights_dict = insight_output.model_dump()
        _save_result(db, job_id, "findings", {"text": insights_dict["findings"]})
        _save_result(db, job_id, "feature_recommendations", {"text": insights_dict["feature_recommendations"]})

        # ── Stage 8 & 9: Model Training & Comparison ─────────────────
        _update_job(db, job_id, current_stage="model_training", progress=70)
        model_results = []
        if plan.target_column and plan.target_column in df_clean.columns and plan.task_type in ("classification", "regression"):
            ml_agent = MLAgent()
            ml_input = MLInput(job_id=job_id, task_type=plan.task_type, target_column=plan.target_column)
            ml_output = ml_agent.train(df_clean, ml_input)
            model_results = [m.model_dump() for m in ml_output.models]
            _save_models(db, job_id, model_results)
        _update_job(db, job_id, current_stage="model_comparison", progress=78)

        # ── Stage 10-11: Regenerate insights with model results ───────
        _update_job(db, job_id, current_stage="business_insights", progress=84)
        insight_input_with_models = InsightInput(
            job_id=job_id,
            task_type=plan.task_type,
            target_column=plan.target_column or "",
        )
        insight_output_final = insight_agent.generate(
            profile, cleaning_report, anomalies, eda, model_results, insight_input_with_models
        )
        insights_dict_final = insight_output_final.model_dump()
        _save_result(db, job_id, "business_insights", {"text": insights_dict_final["business_insights"]})
        _save_result(db, job_id, "executive_summary", {"text": insights_dict_final["executive_summary"]})

        # ── Stage 12: PDF Export ──────────────────────────────────────
        _update_job(db, job_id, current_stage="pdf_export", progress=96)
        report_agent = ReportAgent()
        report_input = ReportInput(job_id=job_id, output_dir=settings.UPLOAD_DIR)
        report_output = report_agent.generate(
            profile=profile,
            cleaning=cleaning_report,
            eda=eda,
            model_results=model_results,
            findings=insights_dict_final["findings"],
            feature_recs=insights_dict_final["feature_recommendations"],
            insights=insights_dict_final["business_insights"],
            summary=insights_dict_final["executive_summary"],
            input_=report_input,
        )
        _save_report(db, job_id, report_output.pdf_path, insights_dict_final["executive_summary"], insights_dict_final["business_insights"])

        # ── Complete ──────────────────────────────────────────────────
        _update_job(db, job_id,
                    status="completed",
                    current_stage="complete",
                    progress=100,
                    completed_at=datetime.now(timezone.utc))

        # Update dataset status
        if ds:
            ds.status = "analyzed"
            db.commit()

        logger.info(f"[{job_id[:8]}] Pipeline completed successfully ✓")
        return {"status": "completed", "job_id": job_id}

    except Exception as exc:
        logger.error(f"[{job_id[:8]}] Pipeline failed: {exc}")
        try:
            _update_job(db, job_id, status="failed", error_message=str(exc)[:500])
        except Exception:
            pass
        raise exc
    finally:
        db.close()
