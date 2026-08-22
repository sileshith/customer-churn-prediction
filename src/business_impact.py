"""
business_impact.py

Translates model scores into a retention-campaign business case:
risk-decile analysis, top-K targeting, revenue at risk, campaign ROI,
and a what-if simulator for testing retention levers on individual
customers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline


def decile_analysis(y_true: pd.Series, y_proba: np.ndarray) -> pd.DataFrame:
    """
    Bucket customers into ten equal-sized groups by predicted churn
    probability (decile 1 = highest risk) and report the churn rate,
    customer count, and cumulative capture rate per decile. This is
    the standard lift-table view of whether the model actually
    concentrates churners at the top of the ranking.
    """
    df = pd.DataFrame({"y_true": np.asarray(y_true), "y_proba": y_proba})
    df["decile"] = pd.qcut(df["y_proba"].rank(method="first", ascending=False), 10, labels=False) + 1

    summary = (
        df.groupby("decile")
        .agg(n_customers=("y_true", "size"), n_churners=("y_true", "sum"))
        .reset_index()
    )
    summary["churn_rate"] = summary["n_churners"] / summary["n_customers"]
    summary["cumulative_churners"] = summary["n_churners"].cumsum()
    total_churners = summary["n_churners"].sum()
    summary["cumulative_capture_rate"] = summary["cumulative_churners"] / total_churners
    return summary


def top_k_capture(y_true: pd.Series, y_proba: np.ndarray, k_pct: float = 0.2) -> dict:
    """
    If the retention team can only act on the top k_pct of customers
    by predicted risk, how many are actually targeted, how many of the
    true churners does that capture, and what fraction of all churners
    does that represent.
    """
    n = len(y_true)
    n_targeted = int(round(n * k_pct))
    order = np.argsort(-y_proba)
    top_idx = order[:n_targeted]
    y_true_arr = np.asarray(y_true)
    n_captured = int(y_true_arr[top_idx].sum())
    total_churners = int(y_true_arr.sum())
    return {
        "n_targeted": n_targeted,
        "n_true_churners_captured": n_captured,
        "total_churners": total_churners,
        "capture_rate": n_captured / total_churners,
    }


def revenue_at_risk(
    monthly_charges: pd.Series,
    y_proba: np.ndarray,
    threshold: float,
    horizon_months: int = 12,
) -> dict:
    """
    Annualized revenue exposed to churn: for every customer whose
    predicted probability clears the decision threshold, project their
    current MonthlyCharges forward across horizon_months. This is a
    exposure estimate, not a forecast -- it answers "how much revenue
    sits behind the accounts the model is flagging," which is what a
    retention budget gets sized against.
    """
    flagged = np.asarray(y_proba) >= threshold
    n_flagged = int(flagged.sum())
    total_at_risk = float(monthly_charges[flagged].sum() * horizon_months)
    avg_monthly_charge = float(monthly_charges[flagged].mean()) if n_flagged else 0.0
    return {
        "n_flagged": n_flagged,
        "avg_monthly_charge": avg_monthly_charge,
        "horizon_months": horizon_months,
        "total_revenue_at_risk": total_at_risk,
    }


def campaign_roi(
    n_true_churners_captured: int,
    avg_monthly_charge: float,
    retention_cost_per_customer: float,
    retention_success_rate: float,
    n_targeted: int,
    horizon_months: int = 12,
) -> dict:
    """
    Net ROI for a targeted retention campaign built on the model's
    ranking. Campaign cost is incurred for every targeted customer
    (n_targeted); revenue saved only accrues for the true churners
    among them who are successfully retained (n_true_churners_captured
    x retention_success_rate). This deliberately does not credit the
    campaign for customers who were never going to churn.
    """
    campaign_cost = n_targeted * retention_cost_per_customer
    customers_retained = n_true_churners_captured * retention_success_rate
    revenue_saved = customers_retained * avg_monthly_charge * horizon_months
    net_benefit = revenue_saved - campaign_cost
    roi_multiple = revenue_saved / campaign_cost if campaign_cost else float("nan")
    return {
        "campaign_cost": campaign_cost,
        "customers_retained_est": customers_retained,
        "revenue_saved": revenue_saved,
        "net_benefit": net_benefit,
        "roi_multiple": roi_multiple,
    }


def what_if_simulator(pipeline: Pipeline, customer: pd.DataFrame, changes: dict) -> dict:
    """
    Score one customer as-is, apply a dict of hypothetical feature
    overrides (e.g. {"Contract": "Two year", "TechSupport": 1}), and
    score the modified version. Used in Section 5 to show how much a
    specific retention lever (contract upgrade, add-on service) would
    be expected to move an individual customer's churn probability.
    """
    baseline_proba = float(pipeline.predict_proba(customer)[:, 1][0])

    modified = customer.copy()
    for feature, new_value in changes.items():
        if feature not in modified.columns:
            raise KeyError(f"'{feature}' is not a column in the customer record.")
        modified[feature] = new_value
        if feature in ("OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
                       "StreamingTV", "StreamingMovies") and "TotalServicesSubscribed" in modified.columns:
            service_cols = ["OnlineSecurity", "OnlineBackup", "DeviceProtection",
                             "TechSupport", "StreamingTV", "StreamingMovies"]
            modified["TotalServicesSubscribed"] = modified[service_cols].sum(axis=1)

    new_proba = float(pipeline.predict_proba(modified)[:, 1][0])
    return {
        "baseline_probability": baseline_proba,
        "simulated_probability": new_proba,
        "absolute_change": new_proba - baseline_proba,
        "changes_applied": changes,
    }
