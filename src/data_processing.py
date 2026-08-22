"""
data_processing.py

Reusable data loading and feature engineering functions for the
customer churn prediction project. Importing these functions into
the notebook (or a future Streamlit app / batch scoring job) keeps
the transformation logic in one place instead of duplicated across
notebook cells.
"""

from pathlib import Path

import numpy as np
import pandas as pd

SERVICE_COLUMNS = [
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
]

NUMERIC_FEATURES = [
    "tenure",
    "MonthlyCharges",
    "TotalCharges",
    "ChargeRatio",
    "TotalServicesSubscribed",
]


def load_raw_data(path: str | Path) -> pd.DataFrame:
    """Load the raw Telco churn CSV from disk."""
    return pd.read_csv(path)


def clean_and_engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw Telco churn data and add a small set of engineered
    features. Returns a new DataFrame; the input is not modified.

    Steps:
    - Drop the customer identifier (not predictive, and a source of leakage
      risk if accidentally one-hot encoded).
    - Coerce TotalCharges to numeric; a handful of rows ship as blank
      strings for customers with zero tenure, which become 0 here.
    - Add ChargeRatio, a rough proxy for whether a customer is paying
      more per month than their accumulated history would suggest.
    - Bucket tenure into four bands for easier interpretation downstream.
    - Collapse the six add-on service columns into a single count of
      subscribed services.
    """
    df = df.copy()

    if "customerID" in df.columns:
        df = df.drop(columns=["customerID"])

    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"] = df["TotalCharges"].fillna(0)

    df["ChargeRatio"] = df["MonthlyCharges"] / (df["TotalCharges"] + 1)

    df["TenureBucket"] = pd.cut(
        df["tenure"],
        bins=[-1, 12, 24, 48, 72],
        labels=["0-1-year", "1-2-years", "2-4-years", "4+-years"],
    )

    df[SERVICE_COLUMNS] = df[SERVICE_COLUMNS].replace(
        {"Yes": 1, "No": 0, "No internet service": 0}
    )
    df["TotalServicesSubscribed"] = df[SERVICE_COLUMNS].sum(axis=1)

    return df


def get_feature_lists(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """
    Split a feature-engineered DataFrame's columns (excluding the target)
    into numeric and categorical feature lists for use in a
    ColumnTransformer.
    """
    feature_columns = [c for c in df.columns if c != "Churn"]
    categorical_features = [c for c in feature_columns if c not in NUMERIC_FEATURES]
    return NUMERIC_FEATURES, categorical_features


def encode_target(series: pd.Series) -> pd.Series:
    """Map the Yes/No Churn column to 1/0."""
    return series.map({"Yes": 1, "No": 0})


if __name__ == "__main__":
    raw_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
    raw = load_raw_data(raw_path)
    engineered = clean_and_engineer_features(raw)
    out_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "churn_engineered.csv"
    engineered.to_csv(out_path, index=False)
    print(f"Wrote engineered features for {len(engineered):,} rows to {out_path}")
