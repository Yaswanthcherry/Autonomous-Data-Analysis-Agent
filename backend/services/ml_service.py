"""
ML training service — auto task detection, multi-model training, comparison
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score,
    mean_squared_error, r2_score, mean_absolute_error,
)
from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
from loguru import logger
import warnings
warnings.filterwarnings("ignore")


class MLService:
    def train(self, df: pd.DataFrame, task_type: str, target_col: str) -> list[dict]:
        logger.info(f"Training ML models. Task: {task_type}, Target: {target_col}")

        df = df.copy().dropna(subset=[target_col])
        X = df.drop(columns=[target_col])
        y = df[target_col]

        # Encode categoricals in features
        X = pd.get_dummies(X, drop_first=True)
        X = X.select_dtypes(include=[np.number]).fillna(0)

        if len(X) < 20:
            return []

        if task_type == "classification":
            le = LabelEncoder()
            y = le.fit_transform(y.astype(str))
            models = self._get_classifiers()
            scorer = self._score_classifier
        else:
            y = pd.to_numeric(y, errors="coerce").fillna(y.median())
            models = self._get_regressors()
            scorer = self._score_regressor

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        results = []
        for name, model in models:
            try:
                pipe = Pipeline([("scaler", StandardScaler()), ("model", model)])
                pipe.fit(X_train, y_train)
                y_pred = pipe.predict(X_test)
                metrics = scorer(y_test, y_pred, pipe, X_test, task_type)
                fi = self._feature_importance(model, X.columns.tolist())
                results.append({
                    "model_name": name,
                    "task_type": task_type,
                    "metrics": metrics,
                    "feature_importance": fi,
                })
                logger.info(f"  {name}: {metrics}")
            except Exception as e:
                logger.warning(f"  {name} failed: {e}")

        # Mark best model
        if results:
            if task_type == "classification":
                best = max(results, key=lambda r: r["metrics"].get("f1", 0))
            else:
                best = max(results, key=lambda r: r["metrics"].get("r2", -999))
            best["is_best"] = True

        return results

    def _get_classifiers(self):
        return [
            ("Logistic Regression", LogisticRegression(max_iter=1000, random_state=42)),
            ("Random Forest", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)),
            ("XGBoost", XGBClassifier(n_estimators=100, random_state=42,
                                       eval_metric="logloss", verbosity=0)),
            ("LightGBM", LGBMClassifier(n_estimators=100, random_state=42, verbose=-1)),
        ]

    def _get_regressors(self):
        return [
            ("Linear Regression", LinearRegression()),
            ("Ridge Regression", Ridge(alpha=1.0)),
            ("Random Forest", RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)),
            ("XGBoost", XGBRegressor(n_estimators=100, random_state=42, verbosity=0)),
            ("LightGBM", LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)),
        ]

    def _score_classifier(self, y_true, y_pred, pipe, X_test, task_type) -> dict:
        metrics = {
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "f1": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        }
        try:
            proba = pipe.predict_proba(X_test)
            if proba.shape[1] == 2:
                metrics["roc_auc"] = round(float(roc_auc_score(y_true, proba[:, 1])), 4)
            else:
                metrics["roc_auc"] = round(float(roc_auc_score(
                    y_true, proba, multi_class="ovr", average="weighted"
                )), 4)
        except Exception:
            pass
        return metrics

    def _score_regressor(self, y_true, y_pred, pipe, X_test, task_type) -> dict:
        return {
            "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 4),
            "mae": round(float(mean_absolute_error(y_true, y_pred)), 4),
            "r2": round(float(r2_score(y_true, y_pred)), 4),
        }

    def _feature_importance(self, model, feature_names: list) -> dict:
        try:
            if hasattr(model, "feature_importances_"):
                imp = model.feature_importances_
                return dict(sorted(
                    zip(feature_names, imp.tolist()),
                    key=lambda x: x[1], reverse=True
                )[:20])
            if hasattr(model, "coef_"):
                coef = np.abs(model.coef_).flatten()[:len(feature_names)]
                return dict(sorted(
                    zip(feature_names, coef.tolist()),
                    key=lambda x: x[1], reverse=True
                )[:20])
        except Exception:
            pass
        return {}
