import pandas as pd
import numpy as np
import pytest
from services.data_profiler import DataProfiler
from services.data_cleaner import DataCleaner
from services.anomaly_detector import AnomalyDetector
from services.eda_service import EDAService
from services.ml_service import MLService


@pytest.fixture
def sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        "age": np.random.randint(18, 80, 200).astype(float),
        "salary": np.random.normal(50000, 15000, 200),
        "department": np.random.choice(["Sales", "Engineering", "HR", "Finance"], 200),
        "score": np.random.uniform(0, 100, 200),
        "churn": np.random.choice([0, 1], 200),
    })


def test_profiler(sample_df):
    profiler = DataProfiler()
    result = profiler.profile(sample_df)
    assert result["shape"]["rows"] == 200
    assert result["shape"]["cols"] == 5
    assert len(result["columns"]) == 5


def test_profiler_with_nulls():
    df = pd.DataFrame({"a": [1, 2, None, 4], "b": ["x", None, "z", "w"]})
    profiler = DataProfiler()
    result = profiler.profile(df)
    col_a = next(c for c in result["columns"] if c["name"] == "a")
    assert col_a["null_count"] == 1
    assert col_a["null_pct"] == 25.0


def test_cleaner(sample_df):
    df_with_nulls = sample_df.copy()
    df_with_nulls.loc[0:5, "age"] = None
    cleaner = DataCleaner()
    df_clean, report = cleaner.clean(df_with_nulls)
    assert df_clean["age"].isnull().sum() == 0
    assert len(report["actions"]) > 0


def test_cleaner_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2, 3], "b": [4, 4, 5, 6]})
    cleaner = DataCleaner()
    df_clean, report = cleaner.clean(df)
    assert len(df_clean) == 3
    drop_action = next((a for a in report["actions"] if a["action"] == "drop_duplicates"), None)
    assert drop_action is not None


def test_anomaly_detector(sample_df):
    detector = AnomalyDetector()
    result = detector.detect(sample_df)
    assert "iqr" in result
    assert "zscore" in result
    assert "isolation_forest" in result
    assert "count" in result["isolation_forest"]


def test_eda_classification(sample_df):
    eda_svc = EDAService()
    result = eda_svc.analyze(sample_df)
    assert "task_type" in result
    assert "target_candidate" in result
    assert "correlation_matrix" in result


def test_ml_classification(sample_df):
    ml_svc = MLService()
    results = ml_svc.train(sample_df, "classification", "churn")
    assert len(results) > 0
    assert any(m.get("is_best") for m in results)
    for m in results:
        assert "accuracy" in m["metrics"]
        assert "f1" in m["metrics"]


def test_ml_regression(sample_df):
    ml_svc = MLService()
    results = ml_svc.train(sample_df, "regression", "salary")
    assert len(results) > 0
    assert any(m.get("is_best") for m in results)
    for m in results:
        assert "r2" in m["metrics"]
        assert "rmse" in m["metrics"]
