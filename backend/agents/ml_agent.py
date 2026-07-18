"""
MLAgent — machine learning model training and comparison.

Responsibilities (Single Responsibility: ML only):
- Train multiple models (LR, RF, XGBoost, LightGBM)
- Evaluate models with appropriate metrics
- Compare model performance
- Select best model

Does NOT modify data. Uses scikit-learn, XGBoost, LightGBM.
"""
from __future__ import annotations

import pandas as pd
from loguru import logger

from agents.schemas import MLInput, MLOutput, ModelResult
from services.ml_service import MLService


class MLAgent:
    """
    Wraps MLService to produce typed MLOutput.
    Maintains single responsibility while providing agent interface.
    """

    def train(self, df: pd.DataFrame, input_: MLInput) -> MLOutput:
        logger.info(f"[{input_.job_id[:8]}] MLAgent training {input_.task_type} models")

        # Use existing service for core logic
        ml_service = MLService()
        model_results_dict = ml_service.train(df, input_.task_type, input_.target_column)

        # Convert to typed format
        models = []
        best_model = None
        for model_dict in model_results_dict:
            model = ModelResult(
                model_name=model_dict["model_name"],
                task_type=model_dict["task_type"],
                metrics=model_dict["metrics"],
                feature_importance=model_dict.get("feature_importance", {}),
                is_best=model_dict.get("is_best", False),
            )
            models.append(model)
            if model.is_best:
                best_model = model

        output = MLOutput(
            job_id=input_.job_id,
            task_type=input_.task_type,
            target_column=input_.target_column,
            models=models,
            best_model=best_model,
        )

        logger.info(f"[{input_.job_id[:8]}] Trained {len(models)} models, best: {best_model.model_name if best_model else 'None'}")
        return output
