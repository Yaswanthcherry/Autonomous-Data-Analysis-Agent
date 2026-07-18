"""
CleanerAgent — data cleaning and preprocessing.

Responsibilities (Single Responsibility: cleaning only):
- Drop empty columns and duplicate rows
- Parse datetime columns
- Fill numeric nulls with median
- Fill categorical nulls with mode
- Track all cleaning actions

Returns cleaned DataFrame and detailed action log.
"""
from __future__ import annotations

import pandas as pd
from loguru import logger

from agents.schemas import CleanerInput, CleanerOutput, CleaningAction
from services.data_cleaner import DataCleaner


class CleanerAgent:
    """
    Wraps DataCleaner service to produce typed CleanerOutput.
    Maintains single responsibility while providing agent interface.
    """

    def clean(self, df: pd.DataFrame, input_: CleanerInput) -> tuple[pd.DataFrame, CleanerOutput]:
        logger.info(f"[{input_.job_id[:8]}] CleanerAgent running on shape {df.shape}")

        # Use existing service for core logic
        cleaner_service = DataCleaner()
        df_clean, report = cleaner_service.clean(df.copy())

        # Convert actions to typed format
        actions = []
        for action_dict in report["actions"]:
            action = CleaningAction(
                action=action_dict["action"],
                column=action_dict.get("column"),
                columns=action_dict.get("columns"),
                count=action_dict.get("count"),
                filled=action_dict.get("filled"),
                value=action_dict.get("value"),
            )
            actions.append(action)

        output = CleanerOutput(
            job_id=input_.job_id,
            original_shape=report["original_shape"],
            cleaned_shape=report["cleaned_shape"],
            actions=actions,
            rows_removed=report["original_shape"][0] - report["cleaned_shape"][0],
        )

        logger.info(f"[{input_.job_id[:8]}] Cleaning complete: {len(actions)} actions")
        return df_clean, output
