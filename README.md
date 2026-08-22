<p align="center">
  <img src="assets/readme-header.png" alt="Customer Churn Prediction. A data-driven retention strategy for subscription telecom. Sileshi Hirpa, Data Science and Business Analytics, Arizona State University." width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB.svg" alt="Python 3.11">
  <img src="https://img.shields.io/badge/scikit--learn-1.5-F7931E.svg" alt="scikit-learn 1.5">
  <img src="https://img.shields.io/badge/XGBoost-2.1-green.svg" alt="XGBoost 2.1">
  <img src="https://img.shields.io/badge/Optuna-4.9-9C27B0.svg" alt="Optuna 4.9">
  <img src="https://img.shields.io/badge/SHAP-Explainable%20AI-brightgreen.svg" alt="SHAP">
</p>

## Executive summary

A ranked retention list, not a leaderboard score. All figures below are one 80/20 holdout (`random_state=42`): **1,409** customers, **374** leavers, **26.5%** base rate.

- **Call list (top 20%):** 282 contacts capture **190 of 374** leavers (**50.8%** capture, **67.4%** precision, **2.5x** a random 20% list).
- **High / Low flag (0.59):** 491 accounts; **$441,250** of 12-month billing sits behind the flag. Exposure, not a loss forecast.
- **Campaign scenario on the 282:** $14,100 cost, $37,043 net, **3.6x**. Assumes $50 per contact and a 35% save rate. Break-even is about **10%**. The 50.8% capture is measured. The 3.6x is not.

| Decision | Number | Role |
|----------|-------:|------|
| Ranked list (top 20%) | **282** people, **190** leavers | Who to call this month |
| Flag at 0.59 | **491** people, **$441,250** | Who is High; sizes exposure |
| Campaign on the 282 | **$14,100** cost, **3.6x** | Scenario until the save rate is measured |

## Problem and objective

**Data.** IBM Telco Customer Churn: 7,043 subscribers, 21 raw fields, 26.5% leavers ([public sample](https://www.kaggle.com/datasets/blastchar/telco-customer-churn); local copy in `data/raw/`).

A model that predicts "stay" for everyone is already **73.5%** accurate and catches **zero** at-risk accounts. This project optimizes PR-AUC, then recall and top-20% capture.

**Objective.** Rank the base by churn risk, explain why each account is High in terms a retention team can act on, and price a campaign on the same holdout rows the model never saw during training.

## Method

CRISP-DM, with three constraints before any model is trusted:

1. **Leakage screen.** Identifier-like columns and suspiciously strong target association are checked first. ChargeRatio looks unique (96.4% distinct values) but is a false positive (Pearson r about 0.026).
2. **Shared preprocessor.** Standard scaling and one-hot encoding in one pipeline, fit only on train. Logistic regression, random forest, and XGBoost see the same features.
3. **Class weights, not SMOTE.** Positive-class weight about 2.77. Train on the real 2.8:1 mix so later calibration is not built on synthetic rows.

**Split.** 80/20 stratified: 5,634 train / 1,409 test. Both stay at 26.5% churn.

**Engineered fields.** ChargeRatio (monthly bill / accumulated history), TenureBucket, and a count of add-on services.

## Exploratory findings

Training set (5,634). Association, not a conversion experiment.

- **Tenure.** Median 10 months among leavers vs 38 among stayers. **55%** of leavers are gone by month 12.
- **Contract.** Churn rates: month-to-month **42.7%**, one-year **11.1%**, two-year **2.9%**. Month-to-month is 55% of the base and **89%** of leavers.
- **Monthly bill.** Median $80 vs $64. The boxes overlap. Fiber sits inside the gap (70% of leavers vs 35% of stayers).
- **ChargeRatio.** Almost uncorrelated with MonthlyCharges (r = -0.04). Bill versus history is a different axis from the raw dollar amount.

The 2.9% two-year rate describes people who already chose a term. It is not a forecast of forcing everyone onto a two-year plan.

## Model selection

| Model | Test PR-AUC | Notes |
|-------|------------:|-------|
| Logistic regression | 0.635 | First before tuning |
| Random forest | 0.621 | Highest precision at the default 0.5 cut |
| XGBoost, untuned | 0.602 | Default trees do not ship |
| **XGBoost, Optuna-tuned** | **0.658** | +0.022 vs logistic; ROC-AUC **0.850** |

Optuna (30 trials, 4-fold on train) picked a shallow regularized tree (depth 4, 450 estimators). Cross-validation peak **0.674**. Holdout **0.658** is the number that counts.

## Decision threshold

F1-max cutoff **0.59** (default 0.50).

- Precision **56.2%**, recall **73.8%**, F1 **0.638**
- Confusion matrix: 276 / 215 / 98 / 820 (TP / FP / FN / TN)
- **491** accounts marked High; that pool sizes the $441,250 exposure
- The **call list is the ranking** (282), not everyone above 0.59

F1 treats a wasted contact and a missed leaver as equal. Under the campaign assumptions they are not ($50 vs a year of bill). 0.59 is a conservative proxy, not a cost-optimal budget.

## Calibration and probability interpretation

| Check | Number |
|-------|--------|
| Brier score | **0.162** (no-skill always-26.5% is 0.195) |
| Mean predicted vs observed | **40.8%** vs **26.5%** |
| Worst-bin gap | **28.6 pp** (predicted 58%, observed 30%; sits on the 0.59 flag) |

The scores over-call churn. Class weighting shifted the scoreboard up. Ranking and flag-then-sum-bills still hold: neither multiplies by p. What-if *levels* (95.1% to 69.3%) sit on that inflated scale. Direction is usable. Do not read 0.59 as a 59% chance.

## Model interpretability (SHAP)

TreeSHAP on the fitted classifier after the preprocessor. Additivity holds to **2.86e-06** across all 1,409 rows: an exact decomposition of this model, including the over-call. Not a causal treatment effect.

<p align="center">
  <img src="assets/figures/01-shap-global.png" alt="Global SHAP importance: month-to-month 21 percent, ChargeRatio 12 percent, fiber 10 percent, two-year 8 percent of top-15 mass." width="720">
</p>

**Figure 1.** Global SHAP importance on the holdout. Mean absolute SHAP is the average size of each feature's push on the raw margin, not a correlation and not a probability. Orange is the top four. Source: `notebooks/01_churn_analysis.ipynb`, section 4.5.

| Lever | Mean abs. SHAP | Share of top-15 mass |
|-------|---------------:|---------------------:|
| Month-to-month dummy | 0.565 | **21%** |
| ChargeRatio | 0.328 | **12%** |
| Fiber optic | 0.278 | **10%** |
| Two-year dummy | 0.210 | **8%** |
| All contract dummies | | **29%** |
| Those four (orange) | | **51%** |

- Contract is the first *family* (it appears twice), then bill-versus-history, then fiber.
- Engineered ChargeRatio outranks raw MonthlyCharges (7%). Electronic check ties the raw bill.
- TotalCharges sits at 3%: once tenure and the monthly rate are in, the lifetime sum is not doing independent work.
- Gender and senior-citizen status are not in the top 15.
- Sign is in the beeswarm. This chart only answers how much. Already-on-term customers are largely protected by the term; offering a contract only fits month-to-month.

**Local check.** Worst holdout row (1-month fiber, $95.10, no support): 95.1% to 81.5% with a one-year contract, then 69.3% after Tech Support and Online Security. Still High versus 0.59. Contract is necessary. It is not sufficient for that row.

## Targeting and lift

<p align="center">
  <img src="assets/figures/02-risk-deciles.png" alt="Holdout risk deciles: churn falls from 76 percent in decile 1 to 1 percent in deciles 9-10. Top 20 percent capture 51 percent of leavers." width="780">
</p>

**Figure 2.** Risk deciles on the same 1,409 holdout customers (decile 1 = highest predicted risk). Orange bars: observed churn rate. Navy line: cumulative share of the 374 leavers. Dashed line: 26.5% base rate. Source: `notebooks/01_churn_analysis.ipynb`, section 5.1.

- Monotonic staircase: **75.9%** churn in decile 1 (107 of 141; **2.86x** base) down to **0.7%** in deciles 9-10.
- That is ranking quality, not calibration. Section 4.4 already showed the scores over-call.
- Top two deciles (20% of customers) hold **50.8%** of leavers (190 of 374). The remaining 184 sit further down. Reaching them means more call capacity, not a different model.

<p align="center">
  <img src="assets/figures/03-top20-targeting.png" alt="At a 20 percent contact budget, random capture is 20 percent, the model captures 50.8 percent, and contacting everyone captures 100 percent." width="680">
</p>

**Figure 3.** Same 20% budget, three policies. Gray is the baseline. Navy is the ranked list (282 names, 190 true leavers, 67.4% precision). Orange is 100% capture at 5x the effort. Source: `notebooks/01_churn_analysis.ipynb`, section 5.2.

- A 20% budget is **282** people. The model puts **190 of 374** leavers on that list.
- **2.5x** random at the same headcount.
- This is the list the campaign prices ($14,100 cost, $37,043 net, 3.6x under a 35% save-rate assumption).
- The 491-person flag is a different job: exposure, not this call list.

| Job | Use | Do not use |
|-----|-----|------------|
| Who to call this month | Top 20% list: 282, 190 leavers (Fig. 3) | The 491-person flag |
| Who is High / Low | Threshold 0.59: 491 accounts | "0.59 means 59%" |
| Billing at risk | $441,250 behind the flag | p x bill x 12 |
| Campaign return | 3.6x on $14,100, 35% save | A budget number until the save rate is measured |

## Repository

```
customer-churn-prediction/
├── data/raw/                 IBM Telco CSV (included)
├── notebooks/01_churn_analysis.ipynb
├── src/
│   ├── data_processing.py    Cleaning and engineered fields
│   ├── data_pipeline.py      Split and shared preprocessor
│   ├── modeling.py           Bake-off, Optuna, threshold, calibration
│   ├── interpretability.py   TreeSHAP, additivity, cohort SHAP
│   └── business_impact.py    Deciles, targeting, exposure, ROI, what-if
├── app/                      Reserved for the scoring UI
├── assets/                   README banner and notebook figures
├── reports/                  Briefing deck
└── requirements.txt
```

The notebook is the narrative. Code in `src/` is what a later app should import. Transformation logic does not live only in a cell.

## Reproduce

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
jupyter lab notebooks/01_churn_analysis.ipynb
```

Run all cells in order. No download step. All holdout numbers use `random_state=42`.

Briefing deck: `reports/Customer_Churn_Prediction.pptx`. Rebuild with `python reports/build_brief_presentation.py`.

## Limitations and next steps

- SHAP and the what-if cell explain and move the model. They do not prove a causal treatment effect.
- $441,250 assumes the current bill continues for a year and treats every flagged account as a leaver. It is exposure, not a loss forecast.
- All metrics are one 80/20 cut. One snapshot: who is at risk now, not whether risk is rising.

**Recommended order.** (1) Pilot the 282 so 35% becomes a measured save rate. (2) Staff the list, not the flag. (3) Promote the champion pipeline into `app/` with the notebook's live controls.

## Citation

IBM. *Telco Customer Churn.* Public sample dataset, 7,043 customers / 21 features.

Chapman et al. (2000). CRISP-DM 1.0. Chen and Guestrin (2016). XGBoost. Akiba et al. (2019). Optuna. Lundberg and Lee (2017). SHAP. Niculescu-Mizil and Caruana (2005). Calibration.

## Author

**Sileshi Hirpa** · Data Science · Business Analytics · Arizona State University

[hirpast@gmail.com](mailto:hirpast@gmail.com) · [linkedin.com/in/sileshi-hirpa](https://www.linkedin.com/in/sileshi-hirpa) · [github.com/sileshith](https://github.com/sileshith) · [hirpadata.com](https://hirpadata.com/)
