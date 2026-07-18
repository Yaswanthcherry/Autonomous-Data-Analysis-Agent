"""
Data cleaning service — nulls, duplicates, type inference, outlier capping
"""
import warnings
import pandas as pd
import numpy as np
from loguru import logger


class DataCleaner:
    def clean(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        report = {
            "original_shape": list(df.shape),
            "actions": [],
        }

        # Drop fully empty columns
        empty_cols = df.columns[df.isnull().all()].tolist()
        if empty_cols:
            df.drop(columns=empty_cols, inplace=True)
            report["actions"].append({"action": "drop_empty_columns", "columns": empty_cols})

        # Drop duplicate rows
        before = len(df)
        df.drop_duplicates(inplace=True)
        dropped = before - len(df)
        if dropped:
            report["actions"].append({"action": "drop_duplicates", "count": dropped})

        # Try to parse datetime columns (infer_datetime_format removed in pandas 2.0)
        for col in df.select_dtypes(include="object").columns:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().sum() > 0.8 * len(df):
                    df[col] = parsed
                    report["actions"].append({"action": "parse_datetime", "column": col})
            except Exception:
                pass

        # Fill numeric nulls with median
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in num_cols:
            n_null = df[col].isnull().sum()
            if n_null > 0:
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                report["actions"].append({
                    "action": "fill_numeric_null",
                    "column": col,
                    "filled": int(n_null),
                    "value": round(float(median_val), 4),
                })

        # Fill categorical nulls with mode
        cat_cols = df.select_dtypes(include="object").columns.tolist()
        for col in cat_cols:
            n_null = df[col].isnull().sum()
            if n_null > 0:
                mode_val = df[col].mode()
                fill_val = mode_val.iloc[0] if not mode_val.empty else "Unknown"
                df[col].fillna(fill_val, inplace=True)
                report["actions"].append({
                    "action": "fill_categorical_null",
                    "column": col,
                    "filled": int(n_null),
                    "value": str(fill_val),
                })

        report["cleaned_shape"] = list(df.shape)
        logger.info(f"Cleaning complete. Actions taken: {len(report['actions'])}")
        return df, report
