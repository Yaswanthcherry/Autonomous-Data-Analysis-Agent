"""
Dataset profiling service — shape, dtypes, nulls, statistics, cardinality
"""
import pandas as pd
import numpy as np
from loguru import logger


class DataProfiler:
    def profile(self, df: pd.DataFrame) -> dict:
        logger.info(f"Profiling dataset: {df.shape}")
        profile = {
            "shape": {"rows": int(df.shape[0]), "cols": int(df.shape[1])},
            "columns": [],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1e6, 3),
            "duplicate_rows": int(df.duplicated().sum()),
        }

        for col in df.columns:
            series = df[col]
            col_info = {
                "name": col,
                "dtype": str(series.dtype),
                "null_count": int(series.isnull().sum()),
                "null_pct": round(series.isnull().mean() * 100, 2),
                "unique_count": int(series.nunique()),
            }

            if pd.api.types.is_numeric_dtype(series):
                desc = series.describe()
                col_info.update({
                    "kind": "numeric",
                    "mean": self._safe_float(desc.get("mean")),
                    "std": self._safe_float(desc.get("std")),
                    "min": self._safe_float(desc.get("min")),
                    "q25": self._safe_float(desc.get("25%")),
                    "median": self._safe_float(desc.get("50%")),
                    "q75": self._safe_float(desc.get("75%")),
                    "max": self._safe_float(desc.get("max")),
                    "skewness": self._safe_float(series.skew()),
                    "kurtosis": self._safe_float(series.kurtosis()),
                })
            elif pd.api.types.is_datetime64_any_dtype(series):
                col_info.update({
                    "kind": "datetime",
                    "min": str(series.min()),
                    "max": str(series.max()),
                })
            else:
                top_values = series.value_counts().head(5).to_dict()
                col_info.update({
                    "kind": "categorical",
                    "top_values": {str(k): int(v) for k, v in top_values.items()},
                })

            profile["columns"].append(col_info)

        return profile

    def _safe_float(self, val) -> float | None:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return None
        return round(float(val), 6)
