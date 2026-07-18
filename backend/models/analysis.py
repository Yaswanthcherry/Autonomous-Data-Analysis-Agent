"""
Analysis models — use JSON type that works on both PostgreSQL (JSONB) and SQLite (tests)
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id"))
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    current_stage: Mapped[str] = mapped_column(String(100), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    dataset: Mapped["Dataset"] = relationship(back_populates="jobs")
    results: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    models: Mapped[list["MLModel"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    charts: Mapped[list["Chart"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    report: Mapped["Report"] = relationship(
        back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_jobs.id"))
    result_type: Mapped[str] = mapped_column(String(50))
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    job: Mapped["AnalysisJob"] = relationship(back_populates="results")


class Chart(Base):
    __tablename__ = "charts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_jobs.id"))
    title: Mapped[str] = mapped_column(String(500))
    chart_type: Mapped[str] = mapped_column(String(50))
    plotly_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    job: Mapped["AnalysisJob"] = relationship(back_populates="charts")


class MLModel(Base):
    __tablename__ = "ml_models"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_jobs.id"))
    model_name: Mapped[str] = mapped_column(String(100))
    task_type: Mapped[str] = mapped_column(String(30))
    metrics: Mapped[dict] = mapped_column(JSON)
    feature_importance: Mapped[dict] = mapped_column(JSON, nullable=True)
    is_best: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    job: Mapped["AnalysisJob"] = relationship(back_populates="models")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_jobs.id"))
    pdf_path: Mapped[str] = mapped_column(String(1000), nullable=True)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=True)
    business_insights: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    job: Mapped["AnalysisJob"] = relationship(back_populates="report")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_jobs.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    job: Mapped["AnalysisJob"] = relationship(back_populates="messages")
