"""
Agent I/O contracts — typed Pydantic schemas for every pipeline agent.
Every agent receives a typed Input and returns a typed Output.
This enforces Single Responsibility and makes agents independently testable.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Shared primitives ──────────────────────────────────────────────────────────

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    kind: str  # numeric | categorical | datetime
    null_count: int
    null_pct: float
    unique_count: int
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    median: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    top_values: Optional[dict[str, int]] = None


class AgentError(BaseModel):
    agent: str
    error: str
    recoverable: bool = True


# ── Planner Agent ──────────────────────────────────────────────────────────────

class PlannerInput(BaseModel):
    file_path: str
    file_type: str  # csv | xlsx | json
    job_id: str


class PlannerOutput(BaseModel):
    job_id: str
    task_type: str          # classification | regression | clustering | time_series
    target_column: Optional[str]
    problem_description: str
    recommended_steps: list[str]
    dataset_summary: dict[str, Any]


# ── Profiler Agent ─────────────────────────────────────────────────────────────

class ProfilerInput(BaseModel):
    job_id: str


class ProfilerOutput(BaseModel):
    job_id: str
    rows: int
    cols: int
    memory_mb: float
    duplicate_rows: int
    columns: list[ColumnProfile]


# ── Cleaner Agent ──────────────────────────────────────────────────────────────

class CleanerInput(BaseModel):
    job_id: str
    original_shape: list[int]


class CleaningAction(BaseModel):
    action: str
    column: Optional[str] = None
    columns: Optional[list[str]] = None
    count: Optional[int] = None
    filled: Optional[int] = None
    value: Optional[Any] = None


class CleanerOutput(BaseModel):
    job_id: str
    original_shape: list[int]
    cleaned_shape: list[int]
    actions: list[CleaningAction]
    rows_removed: int


# ── EDA Agent ─────────────────────────────────────────────────────────────────

class EDAInput(BaseModel):
    job_id: str
    target_column: Optional[str] = None


class EDAOutput(BaseModel):
    job_id: str
    task_type: str
    target_candidate: str
    correlation_matrix: dict[str, Any]
    skewed_columns: list[dict[str, Any]]
    high_cardinality_columns: list[dict[str, Any]]
    class_balance: dict[str, Any]


# ── Visualization Agent ────────────────────────────────────────────────────────

class VisualizationInput(BaseModel):
    job_id: str
    task_type: str
    target_column: str


class ChartSpec(BaseModel):
    title: str
    chart_type: str
    plotly_json: dict[str, Any]


class VisualizationOutput(BaseModel):
    job_id: str
    charts: list[ChartSpec]
    chart_count: int


# ── ML Agent ──────────────────────────────────────────────────────────────────

class MLInput(BaseModel):
    job_id: str
    task_type: str
    target_column: str


class ModelResult(BaseModel):
    model_name: str
    task_type: str
    metrics: dict[str, float]
    feature_importance: dict[str, float] = Field(default_factory=dict)
    is_best: bool = False


class MLOutput(BaseModel):
    job_id: str
    task_type: str
    target_column: str
    models: list[ModelResult]
    best_model: Optional[ModelResult] = None


# ── Insight Agent ──────────────────────────────────────────────────────────────

class InsightInput(BaseModel):
    job_id: str
    task_type: str
    target_column: str
    best_model: Optional[ModelResult] = None


class InsightOutput(BaseModel):
    job_id: str
    findings: str
    feature_recommendations: str
    business_insights: str
    executive_summary: str


# ── Report Agent ──────────────────────────────────────────────────────────────

class ReportInput(BaseModel):
    job_id: str
    output_dir: str


class ReportOutput(BaseModel):
    job_id: str
    pdf_path: str
    page_count: int


# ── Pipeline context (passed between agents) ──────────────────────────────────

class PipelineContext(BaseModel):
    """Immutable context object threaded through all pipeline agents."""
    job_id: str
    dataset_id: str
    file_path: str
    file_type: str

    planner: Optional[PlannerOutput] = None
    profiler: Optional[ProfilerOutput] = None
    cleaner: Optional[CleanerOutput] = None
    eda: Optional[EDAOutput] = None
    visualization: Optional[VisualizationOutput] = None
    ml: Optional[MLOutput] = None
    insights: Optional[InsightOutput] = None
    report: Optional[ReportOutput] = None

    errors: list[AgentError] = Field(default_factory=list)

    def with_error(self, agent: str, error: str, recoverable: bool = True) -> "PipelineContext":
        """Return a copy with an error appended (immutable pattern)."""
        updated = self.model_copy(deep=True)
        updated.errors.append(AgentError(agent=agent, error=error, recoverable=recoverable))
        return updated
