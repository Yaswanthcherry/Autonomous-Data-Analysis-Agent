"""
ProfilerAgent — dataset profiling and column-level statistics.

Responsibilities (Single Responsibility: profiling only):
- Compute dataset shape and memory usage
- Detect duplicate rows
- Profile each column (dtype, nulls, statistics, cardinality)
- Identify column kind (numeric, categorical, datetime)

Does NOT modify data. Does NOT call external APIs.
"""
from __future__ import annotations

import pandas as pd
from loguru import logger

from agents.schemas import ProfilerInput, ProfilerOutput, ColumnProfile
from services.data_profiler import DataProfiler


class ProfilerAgent:
    """
    Wraps DataProfiler service to produce typed ProfilerOutput.
    Maintains single responsibility while providing agent interface.
    """

    def profile(self, df: pd.DataFrame, input_: ProfilerInput) -> ProfilerOutput:
        logger.info(
            f"[{input_.job_id[:8]}] ProfilerAgent running on shape {df.shape}"
        )

        # Use existing service for core logic
        profiler_service = DataProfiler()
        profile_dict = profiler_service.profile(df)

        # Convert to typed output
        columns = []

        for col_dict in profile_dict["columns"]:

            # Determine whether this column contains numeric data.
            # Date, datetime and categorical columns must not pass
            # string/date values into numeric Pydantic fields.
            dtype = col_dict.get("dtype", "")
            is_numeric = pd.api.types.is_numeric_dtype(dtype)

            column_profile = ColumnProfile(
                name=col_dict["name"],
                dtype=col_dict["dtype"],
                kind=col_dict["kind"],
                null_count=col_dict["null_count"],
                null_pct=col_dict["null_pct"],
                unique_count=col_dict["unique_count"],

                # Numeric statistics only
                mean=col_dict.get("mean") if is_numeric else None,
                std=col_dict.get("std") if is_numeric else None,
                min=col_dict.get("min") if is_numeric else None,
                max=col_dict.get("max") if is_numeric else None,
                median=col_dict.get("median") if is_numeric else None,
                skewness=col_dict.get("skewness") if is_numeric else None,
                kurtosis=col_dict.get("kurtosis") if is_numeric else None,

                # Works for categorical/date columns as well
                top_values=col_dict.get("top_values"),
            )

            columns.append(column_profile)

        output = ProfilerOutput(
            job_id=input_.job_id,
            rows=profile_dict["shape"]["rows"],
            cols=profile_dict["shape"]["cols"],
            memory_mb=profile_dict["memory_mb"],
            duplicate_rows=profile_dict["duplicate_rows"],
            columns=columns,
        )

        logger.info(
            f"[{input_.job_id[:8]}] Profiled {len(columns)} columns"
        )

        return output