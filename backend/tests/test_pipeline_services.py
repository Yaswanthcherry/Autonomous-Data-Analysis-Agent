"""
Integration-style tests for the full service pipeline (no DB, no Celery)
"""
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from services.data_profiler import DataProfiler
from services.data_cleaner import DataCleaner
from services.anomaly_detector import AnomalyDetector
from services.eda_service import EDAService
from services.chart_service import ChartService
from services.ml_service import MLService
from services.pdf_service import PDFService


@pytest.fixture
def rich_df():
    np.random.seed(0)
    n = 300
    df = pd.DataFrame({
        "age": np.random.randint(18, 70, n).astype(float),
        "income": np.random.normal(55000, 20000, n),
        "credit_score": np.random.randint(300, 850, n).astype(float),
        "num_loans": np.random.poisson(2, n).astype(float),
        "region": np.random.choice(["North", "South", "East", "West"], n),
        "employment": np.random.choice(["Full-time", "Part-time", "Self-employed"], n),
        "defaulted": np.random.choice([0, 1], n, p=[0.85, 0.15]),
    })
    df.loc[df.sample(frac=0.05).index, "age"] = np.nan
    df.loc[df.sample(frac=0.03).index, "credit_score"] = np.nan
    df = pd.concat([df, df.sample(5)], ignore_index=True)
    return df


def test_full_pipeline_classification(rich_df):
    profiler = DataProfiler()
    profile = profiler.profile(rich_df)
    assert profile["shape"]["rows"] == len(rich_df)
    assert profile["duplicate_rows"] >= 5

    cleaner = DataCleaner()
    df_clean, cleaning = cleaner.clean(rich_df.copy())
    assert df_clean.isnull().sum().sum() == 0
    assert len(df_clean) < len(rich_df)

    anomalies = AnomalyDetector().detect(df_clean)
    assert "iqr" in anomalies
    assert "isolation_forest" in anomalies
    assert anomalies["isolation_forest"]["count"] >= 0

    eda = EDAService().analyze(df_clean)
    assert eda["task_type"] == "classification"
    assert eda["target_candidate"] == "defaulted"
    assert "correlation_matrix" in eda

    charts = ChartService().generate_all(df_clean, eda)
    assert len(charts) >= 3
    for chart in charts:
        assert "title" in chart
        assert "plotly_json" in chart
        assert "data" in chart["plotly_json"]

    results = MLService().train(df_clean, "classification", "defaulted")
    assert len(results) >= 1
    assert any(result.get("is_best") for result in results)
    best = next(result for result in results if result.get("is_best"))
    assert "accuracy" in best["metrics"]
    assert "f1" in best["metrics"]

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = PDFService().generate(
            job_id="test-job-001",
            profile=profile,
            cleaning=cleaning,
            eda=eda,
            model_results=results,
            findings="Key finding: data is clean.",
            feature_recs="Recommend: use credit_score and income.",
            insights="Insight: high income reduces default risk.",
            summary="Executive summary: solid classification results.",
            output_dir=tmpdir,
        )
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000


def test_full_pipeline_regression():
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        "sqft": np.random.randint(800, 4000, n).astype(float),
        "bedrooms": np.random.randint(1, 6, n).astype(float),
        "bathrooms": np.random.randint(1, 4, n).astype(float),
        "age_years": np.random.randint(0, 50, n).astype(float),
        "neighborhood": np.random.choice(["A", "B", "C"], n),
        "price": np.random.normal(350000, 100000, n),
    })

    df_clean, _ = DataCleaner().clean(df.copy())
    eda = EDAService().analyze(df_clean)
    results = MLService().train(df_clean, "regression", "price")
    assert len(results) >= 1
    best = next((result for result in results if result.get("is_best")), None)
    assert best is not None
    assert "r2" in best["metrics"]
    assert "rmse" in best["metrics"]


def test_anomaly_empty_numeric():
    df = pd.DataFrame({"cat": ["a", "b", "c", "d"]})
    result = AnomalyDetector().detect(df)
    assert set(result) == {"iqr", "zscore", "isolation_forest"}
    assert result["iqr"] == {}
    assert result["zscore"] == {}
    assert result["isolation_forest"]["count"] == 0
    assert result["isolation_forest"]["indices"] == []


def test_profiler_dtypes():
    df = pd.DataFrame({
        "num": [1.0, 2.0, 3.0],
        "cat": ["x", "y", "z"],
        "dt": pd.to_datetime(["2024-01-01", "2024-06-01", "2024-12-01"]),
    })
    profile = DataProfiler().profile(df)
    kinds = {column["name"]: column["kind"] for column in profile["columns"]}
    assert kinds["num"] == "numeric"
    assert kinds["cat"] == "categorical"
    assert kinds["dt"] == "datetime"
