"""
PlannerAgent — autonomous dataset analysis and workflow planning.

Responsibilities (Single Responsibility: planning only):
- Detect dataset type (tabular, time-series)
- Detect target column candidate
- Detect problem type: classification | regression | clustering | time_series
- Recommend preprocessing steps
- Produce a PlannerOutput that guides all downstream agents

Does NOT modify data. Does NOT call external APIs.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from loguru import logger

from agents.schemas import PlannerInput, PlannerOutput


# Ordered from strongest semantic signal to fallback keywords. A tuple is
# intentional: iterating a frozenset made target selection nondeterministic.
_TARGET_KEYWORDS: tuple[str, ...] = (
    "target", "label", "class", "outcome", "result", "y",
    "churn", "status", "survived", "default", "fraud",
    "price", "salary", "revenue", "sales", "cost", "score",
    "rating", "value", "demand", "quantity",
)

# Keywords that indicate time-series datasets
_DATETIME_TARGET_KEYWORDS: frozenset[str] = frozenset({
    "date", "time", "timestamp", "datetime", "period", "month", "year", "week",
})


class PlannerAgent:
    """
    Analyzes a DataFrame and produces a structured execution plan.
    All logic is deterministic — no LLM calls needed at planning stage.
    """

    def plan(self, df: pd.DataFrame, input_: PlannerInput) -> PlannerOutput:
        logger.info(f"[{input_.job_id[:8]}] PlannerAgent running on shape {df.shape}")

        target = self._detect_target(df)
        task_type = self._detect_task_type(df, target)
        steps = self._recommend_steps(df, task_type, target)
        summary = self._dataset_summary(df, target, task_type)
        description = self._describe_problem(df, target, task_type)

        output = PlannerOutput(
            job_id=input_.job_id,
            task_type=task_type,
            target_column=target,
            problem_description=description,
            recommended_steps=steps,
            dataset_summary=summary,
        )
        logger.info(
            f"[{input_.job_id[:8]}] Plan: task={task_type}, target={target}, "
            f"steps={len(steps)}"
        )
        return output

    # ── Private helpers ────────────────────────────────────────────────────────

    def _detect_target(self, df: pd.DataFrame) -> str | None:
        """
        Target detection priority:
        1. Explicit target/label/class/outcome columns
        2. Other known target-like names
        3. Last-column fallback
        """
        cols_lower = {str(c).lower(): c for c in df.columns}
        for kw in _TARGET_KEYWORDS:
            if kw in cols_lower:
                return cols_lower[kw]
        return df.columns[-1] if len(df.columns) > 0 else None

    def _detect_task_type(self, df: pd.DataFrame, target: str | None) -> str:
        """Detect classification, regression, clustering, or time series."""
        dt_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
        dt_named = [
            c for c in df.columns
            if any(kw in str(c).lower() for kw in _DATETIME_TARGET_KEYWORDS)
        ]
        if dt_cols or dt_named:
            return "time_series"

        if target is None:
            return "clustering"

        col = df[target]
        if col.nunique() <= 1:
            return "clustering"

        if pd.api.types.is_numeric_dtype(col):
            ratio = col.nunique() / max(len(col), 1)
            if col.nunique() > 20 or ratio > 0.05:
                return "regression"
            return "classification"

        return "classification"

    def _recommend_steps(
        self, df: pd.DataFrame, task_type: str, target: str | None
    ) -> list[str]:
        steps: list[str] = ["profile_dataset", "clean_data", "detect_anomalies", "run_eda"]
        steps.append("generate_visualizations")

        num_count = len(df.select_dtypes(include=[np.number]).columns)
        if num_count >= 2:
            steps.append("statistical_analysis")

        if task_type in ("classification", "regression") and target and len(df) >= 20:
            steps.extend(["train_ml_models", "compare_models", "select_best_model"])

        steps.extend([
            "generate_ai_findings",
            "generate_feature_recommendations",
            "generate_business_insights",
            "generate_executive_summary",
            "export_pdf_report",
        ])
        return steps

    def _dataset_summary(
        self, df: pd.DataFrame, target: str | None, task_type: str
    ) -> dict:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        dt_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
        null_pct = round(df.isnull().mean().mean() * 100, 2)

        summary: dict = {
            "rows": int(df.shape[0]),
            "cols": int(df.shape[1]),
            "numeric_cols": len(num_cols),
            "categorical_cols": len(cat_cols),
            "datetime_cols": len(dt_cols),
            "null_pct": null_pct,
            "duplicate_rows": int(df.duplicated().sum()),
            "target_column": target,
            "task_type": task_type,
        }

        if target and target in df.columns:
            col = df[target]
            summary["target_unique_values"] = int(col.nunique())
            if task_type == "classification":
                vc = col.value_counts(normalize=True).round(3).to_dict()
                summary["class_distribution"] = {str(k): float(v) for k, v in vc.items()}

        return summary

    def _describe_problem(
        self, df: pd.DataFrame, target: str | None, task_type: str
    ) -> str:
        n_rows, n_cols = df.shape
        if task_type == "classification":
            n_classes = df[target].nunique() if target else "unknown"
            return (
                f"Binary/multi-class classification problem with {n_rows} samples, "
                f"{n_cols} features, and {n_classes} target classes. "
                f"Target column: '{target}'."
            )
        if task_type == "regression":
            return (
                f"Regression problem predicting continuous variable '{target}' "
                f"from {n_cols - 1} features across {n_rows} samples."
            )
        if task_type == "time_series":
            return (
                f"Time-series dataset with {n_rows} timesteps and {n_cols} variables. "
                f"Forecasting and temporal pattern analysis recommended."
            )
        return (
            f"Unsupervised clustering dataset with {n_rows} samples "
            f"and {n_cols} features. No clear target column identified."
        )
