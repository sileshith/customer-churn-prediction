"""
modeling.py

Model comparison, Optuna hyperparameter tuning, threshold optimization,
and probability calibration for the customer churn project. Every
model is trained inside a Pipeline(preprocessor -> classifier) so
preprocessing is always fit on the training fold only.
"""

from __future__ import annotations

import numpy as np
import optuna
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

RANDOM_STATE = 42

optuna.logging.set_verbosity(optuna.logging.WARNING)


def get_baseline_models(preprocessor: ColumnTransformer, scale_pos_weight: float) -> dict[str, Pipeline]:
    """
    Three candidate models, each wrapped in the same preprocessing
    pipeline. Class imbalance is handled through class weighting
    (class_weight="balanced" for the sklearn estimators, scale_pos_weight
    for XGBoost) rather than resampling, so every model trains on the
    real class distribution.
    """
    return {
        "Logistic Regression": Pipeline(
            [
                ("preprocessor", preprocessor),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "Random Forest": Pipeline(
            [
                ("preprocessor", preprocessor),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=300,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "XGBoost": Pipeline(
            [
                ("preprocessor", preprocessor),
                (
                    "classifier",
                    XGBClassifier(
                        n_estimators=300,
                        scale_pos_weight=scale_pos_weight,
                        random_state=RANDOM_STATE,
                        eval_metric="logloss",
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def evaluate_model(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series, threshold: float = 0.5) -> dict:
    """Standard classification metrics at a given decision threshold, plus PR-AUC (threshold-free)."""
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    return {
        "ROC-AUC": roc_auc_score(y_test, y_proba),
        "PR-AUC": average_precision_score(y_test, y_proba),
        "Recall": recall_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred, zero_division=0),
        "F1": f1_score(y_test, y_pred),
    }


def compare_models(
    models: dict[str, Pipeline],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[pd.DataFrame, dict[str, Pipeline]]:
    """Fit each candidate model and return a comparison table sorted by PR-AUC."""
    rows = []
    fitted = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        rows.append({"Model": name, **{k: round(v, 4) for k, v in metrics.items()}})
        fitted[name] = model
    table = pd.DataFrame(rows).sort_values("PR-AUC", ascending=False).reset_index(drop=True)
    return table, fitted


def tune_xgboost_optuna(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    preprocessor: ColumnTransformer,
    scale_pos_weight: float,
    n_trials: int = 30,
    cv_folds: int = 4,
) -> optuna.Study:
    """
    Optuna search over XGBoost hyperparameters, scored by mean
    cross-validated PR-AUC (average precision). PR-AUC is used instead
    of ROC-AUC because it is far more sensitive to performance on the
    minority (churn) class, which is what actually drives the business
    prioritization built in Section 5.
    """
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE)

    def objective(trial: optuna.Trial) -> float:
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 150, 600, step=50),
            "max_depth": trial.suggest_int("max_depth", 2, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "gamma": trial.suggest_float("gamma", 0.0, 5.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
        }
        pipe = Pipeline(
            [
                ("preprocessor", preprocessor),
                (
                    "classifier",
                    XGBClassifier(
                        **params,
                        scale_pos_weight=scale_pos_weight,
                        random_state=RANDOM_STATE,
                        eval_metric="logloss",
                        n_jobs=-1,
                    ),
                ),
            ]
        )
        scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="average_precision", n_jobs=-1)
        return float(scores.mean())

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study


def optimize_threshold(y_true: pd.Series, y_proba: np.ndarray) -> tuple[float, pd.DataFrame]:
    """
    Sweep decision thresholds from 0.05 to 0.95 and score precision,
    recall, and F1 at each. Returns the threshold that maximizes F1
    along with the full sweep, which Section 5 plots to show the
    precision/recall trade-off around that point.
    """
    thresholds = np.arange(0.05, 0.96, 0.01)
    rows = []
    for t in thresholds:
        y_pred = (y_proba >= t).astype(int)
        rows.append(
            {
                "threshold": round(float(t), 2),
                "precision": precision_score(y_true, y_pred, zero_division=0),
                "recall": recall_score(y_true, y_pred, zero_division=0),
                "f1": f1_score(y_true, y_pred, zero_division=0),
            }
        )
    sweep = pd.DataFrame(rows)
    best_threshold = float(sweep.loc[sweep["f1"].idxmax(), "threshold"])
    return best_threshold, sweep


def get_calibration_curve(y_true: pd.Series, y_proba: np.ndarray, n_bins: int = 10):
    """Wraps sklearn's calibration_curve for the reliability diagram in Section 5."""
    return calibration_curve(y_true, y_proba, n_bins=n_bins, strategy="quantile")
