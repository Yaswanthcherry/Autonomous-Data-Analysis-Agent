"""
Anomaly detection — IQR, Z-score, Isolation Forest
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from loguru import logger


class AnomalyDetector:
    def detect(self, df: pd.DataFrame) -> dict:
        logger.info("========== ANOMALY DETECTION STARTED ==========")

        try:
            num_df = df.select_dtypes(include=[np.number]).copy()

            if num_df.empty:
                logger.warning("No numeric columns found.")
                return {
                    "iqr": {},
                    "zscore": {},
                    "isolation_forest": {
                        "count": 0,
                        "pct": 0,
                        "indices": []
                    }
                }

            # Remove invalid values
            num_df.replace([np.inf, -np.inf], np.nan, inplace=True)

            # Fill missing values
            num_df = num_df.fillna(num_df.median(numeric_only=True))
            num_df = num_df.fillna(0)

            logger.info(f"Numeric dataframe shape: {num_df.shape}")

            results = {
                "iqr": self._iqr_outliers(num_df),
                "zscore": self._zscore_outliers(num_df),
                "isolation_forest": self._isolation_forest(num_df),
            }

            logger.info("========== ANOMALY DETECTION COMPLETED ==========")

            return results

        except Exception as e:
            logger.exception(f"Anomaly detection failed: {e}")

            return {
                "iqr": {},
                "zscore": {},
                "isolation_forest": {
                    "count": 0,
                    "pct": 0,
                    "indices": [],
                    "error": str(e)
                }
            }

    def _iqr_outliers(self, df: pd.DataFrame):
        outlier_info = {}

        for col in df.columns:
            try:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1

                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr

                mask = (df[col] < lower) | (df[col] > upper)

                outlier_info[col] = {
                    "count": int(mask.sum()),
                    "pct": round(float(mask.mean()) * 100, 2),
                    "lower_bound": float(lower),
                    "upper_bound": float(upper),
                }

            except Exception as e:
                logger.warning(f"IQR failed for {col}: {e}")

        return outlier_info

    def _zscore_outliers(self, df: pd.DataFrame):
        outlier_info = {}

        for col in df.columns:
            try:
                std = df[col].std()

                if std == 0 or np.isnan(std):
                    outlier_info[col] = {
                        "count": 0,
                        "pct": 0
                    }
                    continue

                z = np.abs((df[col] - df[col].mean()) / std)
                mask = z > 3

                outlier_info[col] = {
                    "count": int(mask.sum()),
                    "pct": round(float(mask.mean()) * 100, 2),
                }

            except Exception as e:
                logger.warning(f"Z-score failed for {col}: {e}")

        return outlier_info

    def _isolation_forest(self, df: pd.DataFrame):

        try:

            if len(df) < 20:
                logger.warning("Dataset too small for Isolation Forest.")
                return {
                    "count": 0,
                    "pct": 0,
                    "indices": []
                }

            logger.info("Training Isolation Forest...")

            clf = IsolationForest(
                contamination=0.05,
                random_state=42,
                n_estimators=100,
                n_jobs=1
            )

            preds = clf.fit_predict(df)

            anomaly_indices = np.where(preds == -1)[0].tolist()

            logger.info(f"Isolation Forest finished. Found {len(anomaly_indices)} anomalies.")

            return {
                "count": len(anomaly_indices),
                "pct": round(len(anomaly_indices) / len(df) * 100, 2),
                "indices": anomaly_indices[:100],
            }

        except Exception as e:
            logger.exception(f"Isolation Forest failed: {e}")

            return {
                "count": 0,
                "pct": 0,
                "indices": [],
                "error": str(e)
            }