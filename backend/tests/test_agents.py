"""
Integration tests for agent workflows.
Tests the complete agent-based pipeline orchestration.
"""
import pytest
import pandas as pd
import numpy as np
from agents.planner_agent import PlannerAgent
from agents.profiler_agent import ProfilerAgent
from agents.cleaner_agent import CleanerAgent
from agents.eda_agent import EDAAgent
from agents.visualization_agent import VisualizationAgent
from agents.ml_agent import MLAgent
from agents.schemas import (
    PlannerInput,
    ProfilerInput,
    CleanerInput,
    EDAInput,
    VisualizationInput,
    MLInput,
)


@pytest.fixture
def sample_dataframe():
    np.random.seed(42)
    return pd.DataFrame({
        "age": np.random.randint(18, 80, 100),
        "income": np.random.normal(50000, 15000, 100),
        "score": np.random.rand(100) * 100,
        "category": np.random.choice(["A", "B", "C"], 100),
        "target": np.random.choice([0, 1], 100),
    })


@pytest.fixture
def job_id():
    return "test-job-12345"


class TestPlannerAgent:
    def test_plan_classification(self, sample_dataframe, job_id):
        planner = PlannerAgent()
        input_ = PlannerInput(file_path="test.csv", file_type="csv", job_id=job_id)
        output = planner.plan(sample_dataframe, input_)

        assert output.job_id == job_id
        assert output.task_type == "classification"
        assert output.target_column == "target"
        assert len(output.recommended_steps) > 0
        assert output.dataset_summary["rows"] == len(sample_dataframe)
        assert output.dataset_summary["cols"] == len(sample_dataframe.columns)
        assert output.dataset_summary["target_column"] == "target"

    def test_plan_regression(self, job_id):
        df = pd.DataFrame({
            "x": np.random.rand(100),
            "y": np.random.rand(100) * 100,
        })
        planner = PlannerAgent()
        input_ = PlannerInput(file_path="test.csv", file_type="csv", job_id=job_id)
        output = planner.plan(df, input_)

        assert output.task_type == "regression"
        assert output.target_column == "y"


class TestProfilerAgent:
    def test_profile(self, sample_dataframe, job_id):
        profiler = ProfilerAgent()
        output = profiler.profile(sample_dataframe, ProfilerInput(job_id=job_id))

        assert output.job_id == job_id
        assert output.rows == len(sample_dataframe)
        assert output.cols == len(sample_dataframe.columns)
        assert output.memory_mb > 0
        assert len(output.columns) == len(sample_dataframe.columns)

        for col in output.columns:
            assert col.name in sample_dataframe.columns
            assert col.null_count >= 0
            assert col.null_pct >= 0
            assert col.unique_count > 0


class TestCleanerAgent:
    def test_clean(self, sample_dataframe, job_id):
        df_dirty = sample_dataframe.copy()
        df_dirty.loc[0:5, "age"] = None
        df_dirty.loc[10:15, "income"] = None
        df_dirty = pd.concat([df_dirty, df_dirty.iloc[0:2]], ignore_index=True)

        cleaner = CleanerAgent()
        input_ = CleanerInput(job_id=job_id, original_shape=list(df_dirty.shape))
        df_clean, output = cleaner.clean(df_dirty, input_)

        assert output.job_id == job_id
        assert len(output.actions) > 0
        assert output.rows_removed >= 0
        assert df_clean.shape[0] <= df_dirty.shape[0]
        assert df_clean.isnull().sum().sum() == 0


class TestEDAAgent:
    def test_analyze(self, sample_dataframe, job_id):
        eda_agent = EDAAgent()
        output = eda_agent.analyze(
            sample_dataframe, EDAInput(job_id=job_id, target_column="target")
        )

        assert output.job_id == job_id
        assert output.task_type == "classification"
        assert output.target_candidate == "target"
        assert isinstance(output.correlation_matrix, dict)
        assert isinstance(output.skewed_columns, list)
        assert isinstance(output.high_cardinality_columns, list)


class TestVisualizationAgent:
    def test_generate(self, sample_dataframe, job_id):
        eda_dict = {
            "task_type": "classification",
            "target_candidate": "target",
            "correlation_matrix": {},
            "skewed_columns": [],
            "high_cardinality_columns": [],
            "class_balance": {},
        }
        viz_agent = VisualizationAgent()
        input_ = VisualizationInput(job_id=job_id, task_type="classification", target_column="target")
        output = viz_agent.generate(sample_dataframe, eda_dict, input_)

        assert output.job_id == job_id
        assert output.chart_count > 0
        assert len(output.charts) == output.chart_count
        for chart in output.charts:
            assert chart.title is not None
            assert chart.chart_type is not None
            assert chart.plotly_json is not None


class TestMLAgent:
    def test_train_classification(self, sample_dataframe, job_id):
        ml_agent = MLAgent()
        input_ = MLInput(job_id=job_id, task_type="classification", target_column="target")
        output = ml_agent.train(sample_dataframe, input_)

        assert output.job_id == job_id
        assert output.task_type == "classification"
        assert output.target_column == "target"
        assert len(output.models) > 0
        assert output.best_model is not None
        for model in output.models:
            assert model.model_name is not None
            assert model.task_type == "classification"
            assert len(model.metrics) > 0


class TestAgentIntegration:
    def test_full_agent_workflow(self, sample_dataframe, job_id):
        planner = PlannerAgent()
        plan = planner.plan(
            sample_dataframe,
            PlannerInput(file_path="test.csv", file_type="csv", job_id=job_id),
        )
        assert plan.task_type == "classification"

        profiler = ProfilerAgent()
        profile = profiler.profile(sample_dataframe, ProfilerInput(job_id=job_id))
        assert profile.rows == len(sample_dataframe)

        cleaner = CleanerAgent()
        df_clean, _ = cleaner.clean(
            sample_dataframe,
            CleanerInput(job_id=job_id, original_shape=[profile.rows, profile.cols]),
        )
        assert df_clean.shape[0] <= sample_dataframe.shape[0]

        eda_agent = EDAAgent()
        eda = eda_agent.analyze(
            df_clean, EDAInput(job_id=job_id, target_column=plan.target_column)
        )
        assert eda.task_type == plan.task_type
        assert eda.target_candidate == plan.target_column

        viz_agent = VisualizationAgent()
        charts = viz_agent.generate(
            df_clean,
            eda.model_dump(),
            VisualizationInput(
                job_id=job_id,
                task_type=plan.task_type,
                target_column=plan.target_column or "",
            ),
        )
        assert charts.chart_count > 0

        if plan.task_type in ("classification", "regression") and plan.target_column:
            ml_output = MLAgent().train(
                df_clean,
                MLInput(
                    job_id=job_id,
                    task_type=plan.task_type,
                    target_column=plan.target_column,
                ),
            )
            assert len(ml_output.models) > 0
