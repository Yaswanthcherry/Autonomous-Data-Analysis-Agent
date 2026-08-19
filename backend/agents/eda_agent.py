"""
EDAAgent — exploratory data analysis.

Responsibilities (Single Responsibility: EDA only):
- Compute correlation matrix
- Detect skewed columns
- Detect high cardinality columns
- Analyze class balance
- Identify target candidate and task type

Does NOT modify data. Does NOT call external APIs.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from loguru import logger

from agents.schemas import EDAInput, EDAOutput
from services.eda_service import EDAService


class EDAAgent:
    """
    Wraps EDAService to produce typed EDAOutput.
    Maintains single responsibility while providing agent interface.
    """

    def analyze(self, df: pd.DataFrame, input_: EDAInput) -> EDAOutput:
        logger.info(f"[{input_.job_id[:8]}] EDAAgent running on shape {df.shape}")

        # Use existing service for core logic
        eda_service = EDAService()
        eda_dict = eda_service.analyze(df)

        # Convert to typed output
        output = EDAOutput(
            job_id=input_.job_id,
            task_type=eda_dict["task_type"],
            target_candidate=eda_dict["target_candidate"],
            correlation_matrix=eda_dict["correlation_matrix"],
            skewed_columns=eda_dict["skewed_columns"],
            high_cardinality_columns=eda_dict["high_cardinality_columns"],
            class_balance={str(k): v for k, v in eda_dict["class_balance"].items()},
        )

        logger.info(f"[{input_.job_id[:8]}] EDA complete: task={output.task_type}, target={output.target_candidate}")
        return output
