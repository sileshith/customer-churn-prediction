"""
data_pipeline.py

Leakage auditing, train/test splitting, and preprocessing pipeline
construction for the customer churn project. Builds on top of the
feature engineering in data_processing.py rather than duplicating it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.data_processing import encode_target, get_feature_lists

RANDOM_STATE = 42


def audit_leakage(df: pd.DataFrame, target_col: str = "Churn") -> pd.DataFrame:
    """
    Screen every feature for target leakage before any model is fit.

    Two checks per column:
    - id_like: near-unique values (>95% distinct) that could act as a
      row identifier the model could memorize instead of learn from.
    - assoc: association with the target -- Pearson correlation for
      numeric columns, Cramer's V for categorical columns -- flagged
      when it exceeds 0.9, which is far beyond what any single honest
      predictor should reach on this dataset.

    Returns a DataFrame sorted by association strength, one row per
    feature, so a reviewer can scan the top of the table for anything
    suspicious before trusting downstream model performance.
    """
    y = encode_target(df[target_col]) if df[target_col].dtype == object else df[target_col]
    rows = []
    n = len(df)

    for col in df.columns:
        if col == target_col:
            continue
        series = df[col]
        n_unique = series.nunique(dropna=False)
        id_like = n_unique > 0.95 * n

        if pd.api.types.is_numeric_dtype(series):
            assoc = abs(series.corr(y))
            method = "pearson_r"
        else:
            assoc = _cramers_v(series.astype(str), y)
            method = "cramers_v"

        rows.append(
            {
                "feature": col,
                "dtype": str(series.dtype),
                "n_unique": n_unique,
                "id_like": id_like,
                "association_method": method,
                "association_strength": round(float(assoc), 4),
                "flag": bool(id_like or assoc > 0.9),
            }
        )

    audit = pd.DataFrame(rows).sort_values("association_strength", ascending=False)
    return audit.reset_index(drop=True)


def _cramers_v(a: pd.Series, b: pd.Series) -> float:
    """Bias-corrected Cramer's V for two categorical series."""
    confusion = pd.crosstab(a, b)
    chi2 = _chi2_stat(confusion.values)
    n = confusion.values.sum()
    phi2 = chi2 / n
    r, k = confusion.shape
    phi2_corr = max(0.0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
    r_corr = r - ((r - 1) ** 2) / (n - 1)
    k_corr = k - ((k - 1) ** 2) / (n - 1)
    denom = min((k_corr - 1), (r_corr - 1))
    if denom <= 0:
        return 0.0
    return float(np.sqrt(phi2_corr / denom))


def _chi2_stat(observed: np.ndarray) -> float:
    row_sums = observed.sum(axis=1, keepdims=True)
    col_sums = observed.sum(axis=0, keepdims=True)
    expected = row_sums @ col_sums / observed.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = np.where(expected > 0, (observed - expected) ** 2 / expected, 0.0)
    return float(terms.sum())


def split_features_target(
    df: pd.DataFrame, target_col: str = "Churn"
) -> tuple[pd.DataFrame, pd.Series]:
    """Split an engineered DataFrame into X (features) and y (0/1 target)."""
    X = df.drop(columns=[target_col])
    y = encode_target(df[target_col]) if df[target_col].dtype == object else df[target_col]
    return X, y


def make_train_test_split(
    df: pd.DataFrame,
    target_col: str = "Churn",
    test_size: float = 0.2,
    random_state: int = RANDOM_STATE,
):
    """Stratified train/test split on the engineered DataFrame."""
    X, y = split_features_target(df, target_col)
    return train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    """
    ColumnTransformer that standardizes numeric features and one-hot
    encodes categorical features. Shared by every model in the
    comparison so differences in the results reflect the estimator,
    not the preprocessing.
    """
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), numeric_features),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", drop="if_binary"),
                categorical_features,
            ),
        ]
    )


def get_transformed_feature_names(preprocessor: ColumnTransformer) -> list[str]:
    """Feature names after the ColumnTransformer has been fit, for SHAP labeling."""
    return list(preprocessor.get_feature_names_out())
