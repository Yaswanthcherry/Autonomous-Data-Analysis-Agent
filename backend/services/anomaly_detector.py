"""
Anomaly detection — IQR, Z-score, Isolation Forest
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from loguru import logger


class AnomalyDetector:
    def detect(self, df: pd.DataFrame) -> dict:
        num_df = df.select_dtypes(include=[np.number])
        if num_df.empty:
            return {"method": "none", "anomalies": []}

        results = {
            "iqr": self._iqr_outliers(num_df),
            "zscore": self._zscore_outliers(num_df),
            "isolation_forest": self._isolation_forest(num_df),
        }
        logger.info(f"Anomaly detection complete. IF anomalies: {results['isolation_forest']['count']}")
        return results

    def _iqr_outliers(self, df: pd.DataFrame) -> dict:
        outlier_info = {}
        for col in df.columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            mask = (df[col] < lower) | (df[col] > upper)
            outlier_info[col] = {
                "count": int(mask.sum()),
                "pct": round(float(mask.mean()) * 100, 2),
                "lower_bound": round(float(lower), 4),
                "upper_bound": round(float(upper), 4),
            }
        return outlier_info

    def _zscore_outliers(self, df: pd.DataFrame) -> dict:
        outlier_info = {}
        for col in df.columns:
            z = np.abs((df[col] - df[col].mean()) / (df[col].std() + 1e-9))
            mask = z > 3
            outlier_info[col] = {
                "count": int(mask.sum()),
                "pct": round(float(mask.mean()) * 100, 2),
            }
        return outlier_info

    def _isolation_forest(self, df: pd.DataFrame) -> dict:
        clean_df = df.fillna(df.median())
        if len(clean_df) < 10:
            return {"count": 0, "indices": []}
        clf = IsolationForest(contamination=0.05, random_state=42, n_jobs=-1)
        preds = clf.fit_predict(clean_df)
        anomaly_indices = list(np.where(preds == -1)[0].astype(int))
        return {
            "count": len(anomaly_indices),
            "pct": round(len(anomaly_indices) / len(df) * 100, 2),
            "indices": anomaly_indices[:100],  # cap for storage
        }
