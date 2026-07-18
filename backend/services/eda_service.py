"""
EDA service — correlation, distributions, target analysis
"""
import pandas as pd
import numpy as np
from loguru import logger


class EDAService:
    def analyze(self, df: pd.DataFrame) -> dict:
        num_df = df.select_dtypes(include=[np.number])
        eda = {
            "correlation_matrix": {},
            "skewed_columns": [],
            "high_cardinality_columns": [],
            "target_candidate": None,
            "class_balance": {},
        }

        # Correlation matrix
        if len(num_df.columns) >= 2:
            corr = num_df.corr().round(4)
            eda["correlation_matrix"] = corr.to_dict()

        # Skewness
        for col in num_df.columns:
            skew = float(num_df[col].skew())
            if abs(skew) > 1:
                eda["skewed_columns"].append({"column": col, "skewness": round(skew, 3)})

        # High cardinality
        cat_df = df.select_dtypes(include="object")
        for col in cat_df.columns:
            if cat_df[col].nunique() > 50:
                eda["high_cardinality_columns"].append({
                    "column": col, "unique_count": int(cat_df[col].nunique())
                })

        # Target candidate (last column or column named target/label/class)
        target_keywords = {"target", "label", "class", "outcome", "y", "result", "churn", "status"}
        candidates = [c for c in df.columns if c.lower() in target_keywords]
        if candidates:
            target = candidates[0]
        else:
            target = df.columns[-1]

        eda["target_candidate"] = target
        if df[target].nunique() <= 20:
            eda["class_balance"] = df[target].value_counts().to_dict()

        # Infer task type
        if pd.api.types.is_numeric_dtype(df[target]) and df[target].nunique() > 10:
            eda["task_type"] = "regression"
        else:
            eda["task_type"] = "classification"

        logger.info(f"EDA complete. Task type: {eda['task_type']}, target: {target}")
        return eda
