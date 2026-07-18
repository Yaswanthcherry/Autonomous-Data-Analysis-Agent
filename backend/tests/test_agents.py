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
    """Create a sample DataFrame for testing."""
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
    """Generate a test job ID."""
    return "test-job-12345"


class TestPlannerAgent:
    """Test PlannerAgent functionality."""

    def test_plan_classification(self, sample_dataframe, job_id):
        """Test planning for classification task."""
        planner = PlannerAgent()
        input_ = PlannerInput(file_path="test.csv", file_type="csv", job_id=job_id)
        
        output = planner.plan(sample_dataframe, input_)
        
        assert output.job_id == job_id
        assert output.task_type in ["classification", "regression", "clustering", "time_series"]
        assert output.target_column is not None
        assert len(output.recommended_steps) > 0
        assert "dataset_summary" in output.dataset_summary

    def test_plan_regression(self, job_id):
        """Test planning for regression task."""
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
    """Test ProfilerAgent functionality."""

    def test_profile(self, sample_dataframe, job_id):
        """Test dataset profiling."""
        profiler = ProfilerAgent()
        input_ = ProfilerInput(job_id=job_id)
        
        output = profiler.profile(sample_dataframe, input_)
        
        assert output.job_id == job_id
        assert output.rows == len(sample_dataframe)
        assert output.cols == len(sample_dataframe.columns)
        assert output.memory_mb > 0
        assert len(output.columns) == len(sample_dataframe.columns)
        
        # Check column profiles
        for col in output.columns:
            assert col.name in sample_dataframe.columns
            assert col.null_count >= 0
            assert col.null_pct >= 0
            assert col.unique_count > 0


class TestCleanerAgent:
    """Test CleanerAgent functionality."""

    def test_clean(self, sample_dataframe, job_id):
        """Test data cleaning."""
        # Add some nulls and duplicates
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
        assert df_clean.isnull().sum().sum() == 0  # All nulls should be filled


class TestEDAAgent:
    """Test EDAAgent functionality."""

    def test_analyze(self, sample_dataframe, job_id):
        """Test EDA analysis."""
        eda_agent = EDAAgent()
        input_ = EDAInput(job_id=job_id, target_column="target")
        
        output = eda_agent.analyze(sample_dataframe, input_)
        
        assert output.job_id == job_id
        assert output.task_type in ["classification", "regression"]
        assert output.target_column == "target"
        assert isinstance(output.correlation_matrix, dict)
        assert isinstance(output.skewed_columns, list)
        assert isinstance(output.high_cardinality_columns, list)


class TestVisualizationAgent:
    """Test VisualizationAgent functionality."""

    def test_generate(self, sample_dataframe, job_id):
        """Test chart generation."""
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
        
        # Check chart structure
        for chart in output.charts:
            assert chart.title is not None
            assert chart.chart_type is not None
            assert chart.plotly_json is not None


class TestMLAgent:
    """Test MLAgent functionality."""

    def test_train_classification(self, sample_dataframe, job_id):
        """Test ML model training for classification."""
        ml_agent = MLAgent()
        input_ = MLInput(job_id=job_id, task_type="classification", target_column="target")
        
        output = ml_agent.train(sample_dataframe, input_)
        
        assert output.job_id == job_id
        assert output.task_type == "classification"
        assert output.target_column == "target"
        assert len(output.models) > 0
        assert output.best_model is not None
        
        # Check model metrics
        for model in output.models:
            assert model.model_name is not None
            assert model.task_type == "classification"
            assert len(model.metrics) > 0


class TestAgentIntegration:
    """Integration tests for complete agent workflows."""

    def test_full_agent_workflow(self, sample_dataframe, job_id):
        """Test complete workflow through all agents."""
        
        # Step 1: Planning
        planner = PlannerAgent()
        plan = planner.plan(sample_dataframe, PlannerInput(file_path="test.csv", file_type="csv", job_id=job_id))
        assert plan.task_type is not None
        
        # Step 2: Profiling
        profiler = ProfilerAgent()
        profile = profiler.profile(sample_dataframe, ProfilerInput(job_id=job_id))
        assert profile.rows == len(sample_dataframe)
        
        # Step 3: Cleaning
        cleaner = CleanerAgent()
        df_clean, cleaning = cleaner.clean(sample_dataframe, CleanerInput(job_id=job_id, original_shape=[profile.rows, profile.cols]))
        assert df_clean.shape[0] <= sample_dataframe.shape[0]
        
        # Step 4: EDA
        eda_agent = EDAAgent()
        eda = eda_agent.analyze(df_clean, EDAInput(job_id=job_id, target_column=plan.target_column))
        assert eda.task_type == plan.task_type
        
        # Step 5: Visualization
        viz_agent = VisualizationAgent()
        charts = viz_agent.generate(df_clean, eda.model_dump(), VisualizationInput(job_id=job_id, task_type=plan.task_type, target_column=plan.target_column or ""))
        assert charts.chart_count > 0
        
        # Step 6: ML (if applicable)
        if plan.task_type in ("classification", "regression") and plan.target_column:
            ml_agent = MLAgent()
            ml_output = ml_agent.train(df_clean, MLInput(job_id=job_id, task_type=plan.task_type, target_column=plan.target_column))
            assert len(ml_output.models) > 0
