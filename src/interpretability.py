"""
interpretability.py

SHAP-based explainability for the champion XGBoost pipeline: global
importance, per-customer local explanations, an additivity check that
SHAP values actually sum back to the model's raw output, and cohort
comparisons of what drives churn for different customer segments.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap
from sklearn.pipeline import Pipeline


def build_explainer(pipeline: Pipeline, X_background: pd.DataFrame):
    """
    TreeExplainer built on the fitted XGBoost step, applied to
    already-preprocessed data. Returns the explainer plus the
    transformed background matrix and feature names, since SHAP needs
    to operate on the numeric matrix the classifier actually sees.
    """
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]
    X_transformed = preprocessor.transform(X_background)
    feature_names = list(preprocessor.get_feature_names_out())
    if hasattr(X_transformed, "toarray"):
        X_transformed = X_transformed.toarray()
    explainer = shap.TreeExplainer(classifier)
    return explainer, X_transformed, feature_names


def compute_shap_values(explainer, X_transformed: np.ndarray):
    """Raw SHAP values for a (transformed) feature matrix."""
    return explainer.shap_values(X_transformed)


def verify_additivity(
    explainer, shap_values: np.ndarray, classifier, X_transformed: np.ndarray
) -> dict:
    """
    Confirm SHAP's additivity guarantee: expected_value + sum(shap_values)
    for a row must equal the model's raw margin output for that row.
    A large discrepancy would mean the explainer is being fed the wrong
    inputs (e.g. non-preprocessed data), which would silently invalidate
    every plot in this section.
    """
    import xgboost as xgb

    dmatrix = xgb.DMatrix(X_transformed)
    raw_margin = classifier.get_booster().predict(dmatrix, output_margin=True)
    reconstructed = explainer.expected_value + shap_values.sum(axis=1)
    max_abs_diff = float(np.max(np.abs(raw_margin - reconstructed)))
    return {
        "max_abs_diff": max_abs_diff,
        "passed": max_abs_diff < 1e-3,
        "n_rows_checked": int(X_transformed.shape[0]),
    }


def global_importance(shap_values: np.ndarray, feature_names: list[str], top_n: int = 15) -> pd.DataFrame:
    """Mean |SHAP value| per feature, sorted descending -- the global importance ranking."""
    mean_abs = np.abs(shap_values).mean(axis=0)
    ranking = (
        pd.DataFrame({"feature": feature_names, "mean_abs_shap": mean_abs})
        .sort_values("mean_abs_shap", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return ranking


def cohort_shap_summary(
    shap_values: np.ndarray,
    feature_names: list[str],
    cohort_labels: pd.Series,
    top_n: int = 5,
) -> pd.DataFrame:
    """
    Mean |SHAP value| per feature, computed separately within each
    cohort (e.g. contract type). Lets Section 7 show that the same
    model can be driven by different factors for different customer
    segments, rather than assuming one global explanation fits everyone.
    """
    shap_df = pd.DataFrame(np.abs(shap_values), columns=feature_names)
    shap_df["__cohort__"] = cohort_labels.reset_index(drop=True)

    rows = []
    for cohort, group in shap_df.groupby("__cohort__", observed=True):
        top_features = group.drop(columns="__cohort__").mean().sort_values(ascending=False).head(top_n)
        for rank, (feature, value) in enumerate(top_features.items(), start=1):
            rows.append({"cohort": cohort, "rank": rank, "feature": feature, "mean_abs_shap": value})
    return pd.DataFrame(rows)
