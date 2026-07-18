"""
Integration-style tests for the full service pipeline (no DB, no Celery)
"""
import pandas as pd
import numpy as np
import pytest
from services.data_profiler import DataProfiler
from services.data_cleaner import DataCleaner
from services.anomaly_detector import AnomalyDetector
from services.eda_service import EDAService
from services.chart_service import ChartService
from services.ml_service import MLService
from services.pdf_service import PDFService
import tempfile
import os


@pytest.fixture
def rich_df():
    """Realistic mixed dataset for pipeline testing."""
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
    # Inject some nulls
    df.loc[df.sample(frac=0.05).index, "age"] = np.nan
    df.loc[df.sample(frac=0.03).index, "credit_score"] = np.nan
    # Inject duplicates
    df = pd.concat([df, df.sample(5)], ignore_index=True)
    return df


def test_full_pipeline_classification(rich_df):
    """Run every service stage end-to-end on a classification dataset."""
    # 1. Profile
    profiler = DataProfiler()
    profile = profiler.profile(rich_df)
    assert profile["shape"]["rows"] == len(rich_df)
    assert profile["duplicate_rows"] >= 5

    # 2. Clean
    cleaner = DataCleaner()
    df_clean, cleaning = cleaner.clean(rich_df.copy())
    assert df_clean.isnull().sum().sum() == 0
    assert len(df_clean) < len(rich_df)  # duplicates removed

    # 3. Anomaly
    detector = AnomalyDetector()
    anomalies = detector.detect(df_clean)
    assert "iqr" in anomalies
    assert "isolation_forest" in anomalies
    assert anomalies["isolation_forest"]["count"] >= 0

    # 4. EDA
    eda_svc = EDAService()
    eda = eda_svc.analyze(df_clean)
    assert eda["task_type"] in ("classification", "regression")
    assert "target_candidate" in eda
    assert "correlation_matrix" in eda

    # 5. Charts
    chart_svc = ChartService()
    charts = chart_svc.generate_all(df_clean, eda)
    assert len(charts) >= 3
    for c in charts:
        assert "title" in c
        assert "plotly_json" in c
        assert "data" in c["plotly_json"]

    # 6. ML
    ml_svc = MLService()
    results = ml_svc.train(df_clean, "classification", "defaulted")
    assert len(results) >= 1
    assert any(r.get("is_best") for r in results)
    best = next(r for r in results if r.get("is_best"))
    assert "accuracy" in best["metrics"]
    assert "f1" in best["metrics"]

    # 7. PDF
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_svc = PDFService()
        pdf_path = pdf_svc.generate(
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
        assert os.path.getsize(pdf_path) > 1000  # non-empty PDF


def test_full_pipeline_regression():
    """Run pipeline on a regression dataset."""
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

    cleaner = DataCleaner()
    df_clean, _ = cleaner.clean(df.copy())

    eda_svc = EDAService()
    eda = eda_svc.analyze(df_clean)

    ml_svc = MLService()
    results = ml_svc.train(df_clean, "regression", "price")
    assert len(results) >= 1
    best = next((r for r in results if r.get("is_best")), None)
    assert best is not None
    assert "r2" in best["metrics"]
    assert "rmse" in best["metrics"]


def test_anomaly_empty_numeric():
    """Anomaly detector handles non-numeric only datasets gracefully."""
    df = pd.DataFrame({"cat": ["a", "b", "c", "d"]})
    detector = AnomalyDetector()
    result = detector.detect(df)
    assert result == {"method": "none", "anomalies": []}


def test_profiler_dtypes():
    """Profiler correctly categorises numeric, categorical, datetime columns."""
    df = pd.DataFrame({
        "num": [1.0, 2.0, 3.0],
        "cat": ["x", "y", "z"],
        "dt": pd.to_datetime(["2024-01-01", "2024-06-01", "2024-12-01"]),
    })
    profile = DataProfiler().profile(df)
    kinds = {c["name"]: c["kind"] for c in profile["columns"]}
    assert kinds["num"] == "numeric"
    assert kinds["cat"] == "categorical"
    assert kinds["dt"] == "datetime"
