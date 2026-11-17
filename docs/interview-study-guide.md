# Data Science Interview Study Guide

Prepared from the files in this workspace for **Sileshi Hirpa** (Data Science and Business Analytics, Arizona State University). Every project number below comes from `customer-churn-prediction`: the notebook `notebooks/01_churn_analysis.ipynb`, the modules in `src/`, the briefing builders in `reports/`, and `README.md`. Standard interview topics that do not appear in those files are labeled **Gap** so you do not claim experience you cannot open on your machine.

---

## Phase 1 — Inventory

### What was actually in the workspace

A recursive scan of `/workspace` found **one repository**, not a `Desktop/ASU` course tree. There are no syllabi, no course-code folders (no CIS, WPC, STP, or IEE directories), no homework sets, no SQL scripts, no Excel workbooks, no PySpark jobs, and no research notes on fraud, grid risk, or graph / scientific ML.

Git history is three commits on `main`, all about publishing this portfolio project. Author line in the README: Sileshi Hirpa, Arizona State University.

| Item | Location | What it is |
| --- | --- | --- |
| Portfolio project | repo root, `README.md` | Customer churn ranking for a subscription telecom. IBM Telco sample, 7,043 customers, 21 raw fields. |
| Analysis notebook | `notebooks/01_churn_analysis.ipynb` | 93 cells. CRISP-DM path: problem, leakage screen, EDA, three-model bake-off, Optuna, threshold, calibration, TreeSHAP, deciles, campaign math, ipywidgets rescoring, conclusions. |
| Feature engineering | `src/data_processing.py` | Drop `customerID`. Coerce `TotalCharges`. Build `ChargeRatio`, `TenureBucket`, `TotalServicesSubscribed`. |
| Leakage, split, preprocessor | `src/data_pipeline.py` | Identifier screen, Pearson / bias-corrected Cramér's V, stratified 80/20, shared `ColumnTransformer`. |
| Modeling | `src/modeling.py` | Class-weighted logistic regression, random forest, XGBoost. Optuna on PR-AUC. F1 threshold sweep. Calibration curve. |
| Explanations | `src/interpretability.py` | `shap.TreeExplainer`, additivity check, global mean \|SHAP\|, cohort rankings. |
| Decision math | `src/business_impact.py` | Decile lift, top-20% capture, 12-month exposure, campaign ROI, single-row what-if. |
| Stakeholder deck | `reports/Customer_Churn_Prediction.pptx` plus `reports/build_brief_presentation.py` | Briefing that leads with a call list. Speaker notes tell you which numbers are measured and which are assumptions. |
| Data | `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` | 7,043 rows. Churn 1,869 / 7,043 = 26.5%. Eleven blank `TotalCharges`, all with `tenure = 0`. |
| Dependencies declared, lightly used or unused | `requirements.txt` | `imbalanced-learn` is installed and then deliberately skipped. `streamlit` and `plotly` are listed. The live UI in the notebook is **ipywidgets**. There is no `app/` directory. |

### Dataset fields you should be able to name from memory

`customerID`, `gender`, `SeniorCitizen`, `Partner`, `Dependents`, `tenure`, `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`, `Contract`, `PaperlessBilling`, `PaymentMethod`, `MonthlyCharges`, `TotalCharges`, `Churn`.

Engineered: `ChargeRatio = MonthlyCharges / (TotalCharges + 1)`, `TenureBucket` with cuts at 12 / 24 / 48 / 72 months, `TotalServicesSubscribed` = count of six add-ons after mapping `Yes` → 1 and both `No` and `No internet service` → 0.

### Locked holdout numbers (random_state=42)

Use these exactly. Interviewers notice rounded fiction.

| Fact | Number | Where it lives |
| --- | --- | --- |
| Split | 5,634 train / 1,409 test, both 26.5% churn | Stratified `train_test_split` |
| Train mix | 4,139 stayed, 1,495 left. `scale_pos_weight` = 4,139 / 1,495 ≈ **2.77** | Notebook §3 |
| Tenure | Median 10 months (leavers) vs 38 (stayers). 822 / 1,495 = **55%** of training leavers gone by month 12 | §3 |
| Contract, training | Month-to-month **42.7%** (3,102 accounts, 89% of leavers), one-year **11.1%**, two-year **2.9%** | §3 |
| Bill | Median $80 leavers vs $64 stayers. Fiber: 70% of leavers vs 35% of stayers | §3 |
| Correlations | tenure × TotalCharges **0.83**. ChargeRatio × MonthlyCharges **−0.04** | §3 |
| Untuned test PR-AUC | Logistic **0.635**, forest **0.621**, XGBoost **0.602**. ROC-AUC 0.842 / 0.826 / 0.811 | §4.1 |
| Optuna | 30 TPE trials, 4-fold PR-AUC on train only. Best CV **0.674** at trial 6. Depth **4**, **450** trees, `min_child_weight` **10**, gamma / L1 / L2 ≈ **3.9 / 5.7 / 3.8** | §4.2 |
| Champion holdout | Tuned XGBoost PR-AUC **0.658**, ROC-AUC **0.850**. Beats logistic by 0.022 | §4.2 |
| Flag | F1-max threshold **0.59**. Precision 56.2%, recall 73.8%, F1 0.638. Confusion **276 / 215 / 98 / 820** (TP/FP/FN/TN). **491** accounts flagged | §4.3 |
| Calibration | Brier **0.162** vs no-skill **0.195**. Mean predicted **40.8%** vs observed **26.5%**. Worst bin: predicted 58%, observed 30% (**28.6 pp**) | §4.4 |
| SHAP | Additivity max abs diff **2.86e-06** on all 1,409 rows. Month-to-month 21% of top-15 mass, ChargeRatio 12%, fiber 10%, two-year 8%. Contract family 29%. Top four 51% | §4.5 |
| Deciles | Decile 1 churn **75.9%** (107/141, 2.86× base). Top 20% holds **190/374 = 50.8%** of test leavers. Bottom 40% holds 6 of 374 | §5.1 |
| Call list | 282 contacts, 190 true leavers, precision **67.4%**, **2.5×** a random 20% list | §5.2 |
| Exposure | 491 flagged × mean monthly **$74.89** × 12 = **$441,250** | §5.3 |
| Scenario | Cost 282 × $50 = **$14,100**. Saved ≈ 190 × 0.35 × $64.09 × 12 = **$51,143**. Net **$37,043**. Multiple **3.6×**. Break-even save rate ≈ **10%** | §5.4 |
| What-if, worst holdout row | 1-month fiber, $95.10, no support: **95.1% → 81.5%** (one-year) → **69.3%** (+ Tech Support and Online Security). Still above 0.59 | §5.5 |

### Strongest material

This is a **decision memo with a model attached**, which is rarer in student portfolios than another accuracy table.

1. **Metric tied to a constraint.** Accuracy is dismissed because a constant "stay" classifier is already 73.5% accurate and catches nobody. The success metric is PR-AUC, then a capacity-constrained capture rate.
2. **Leakage screen before fitting**, including the judgment to keep `ChargeRatio` after it tripped an identifier rule (96.4% unique, Pearson r ≈ 0.026).
3. **One preprocessor, fit inside the pipeline**, so the three-model comparison is about the estimator.
4. **Class weights chosen over SMOTE** (`imbalanced-learn` is in `requirements.txt` and unused) specifically so calibration is not built on synthetic rows.
5. **Tuning did not touch the test set.** Optuna's 0.674 is labeled as CV. The number you defend is holdout 0.658.
6. **Calibration is measured and then allowed to change the claim.** Scores over-call. Ranking and "sum the actual bills behind a flag" stay valid. "0.59 means a 59% chance" does not. Platt or isotonic is reserved for a future `p × bill` price.
7. **SHAP is checked**, not just plotted. Additivity to 2.86e-06. Global, beeswarm direction, one waterfall, and a cohort split that changes the offer: term upgrades fit month-to-month accounts; people already on a term are protected by that term.
8. **Two different operational objects.** The 282-person ranking is who to call. The 491-person flag is exposure. The 3.6× multiple is a scenario with a replaceable 35% save rate. The deck's speaker notes say the same thing.

### What a full ASU folder would usually add, and is absent here

Fraud detection, energy or grid risk, PySpark, GNN or SciML research papers, SQL case work, Excel dashboards, and a graded statistics sequence (t-tests, ANOVA write-ups, designed experiments) are **not in this workspace**. If those projects live under `Desktop/ASU` on another machine, open that folder in Cursor and rerun this pass. Until then, interview answers about those topics stay conceptual. Do not narrate them as personal projects.

---

## 1. Personal skill inventory

### Ranked strengths, from the files

| Rank | Skill | Evidence you can open |
| --- | --- | --- |
| 1 | Turning a classifier into an action under a capacity constraint | Top 20% list: 282 people, 190 of 374 leavers, 2.5× random. `top_k_capture` in `src/business_impact.py`. |
| 2 | Choosing a metric that matches the decision | PR-AUC over accuracy and over ROC-AUC. Stated in §1 and used as the Optuna objective (`scoring="average_precision"`). |
| 3 | Leakage control and reproducible preprocessing | `audit_leakage`, drop `customerID`, `Pipeline(preprocessor → classifier)`, `random_state=42`. |
| 4 | Imbalance handling with an eye on calibration | `class_weight="balanced"`, `scale_pos_weight≈2.77`, explicit rejection of resampling, then a reliability diagram. |
| 5 | Model selection with a simple baseline kept honest | Logistic wins the untuned bake-off (0.635). Tuned XGBoost only ships after it clears 0.658 on holdout. |
| 6 | Hyperparameter search that cannot see the test set | 30-trial TPE, 4-fold `StratifiedKFold` on train, shallow regularized tree. |
| 7 | Explainability a retention agent can say out loud | TreeSHAP. "Bill high relative to tenure, month-to-month, fiber, electronic check." |
| 8 | Separating measured results from assumptions | 50.8% capture is measured. 3.6× is not. Break-even ≈ 10%. |
| 9 | Feature engineering aimed at a mechanism | `ChargeRatio` is almost uncorrelated with `MonthlyCharges` (r = −0.04) and later outranks it in SHAP (12% vs 7%). |
| 10 | Stakeholder writing | README executive summary, three-job table (call / flag / dollars), briefing deck with speaker notes. |

### Tools with real use in this repo

| Tool | How you used it | How hard you can lean on it |
| --- | --- | --- |
| Python 3.11 | Whole project | Strong |
| pandas | Load, coerce, `qcut` deciles, groupbys, crosstabs | Strong |
| NumPy | Ranking, masks, chi-square arithmetic inside Cramér's V | Solid |
| scikit-learn | `ColumnTransformer`, `Pipeline`, logistic regression, random forest, stratified split and CV, precision/recall/F1, average precision, ROC-AUC, `calibration_curve` | Strong for tabular classification |
| XGBoost 2.1 | Champion model, raw-margin predictions for the SHAP check | Strong for this problem size |
| Optuna 4.9 | TPE, 30 trials, PR-AUC | You have one real search. Know the search space in `tune_xgboost_optuna`. |
| SHAP 0.46 | `TreeExplainer` on the booster after the preprocessor | Strong for trees. KernelSHAP on the logistic model is a gap. |
| matplotlib / seaborn | EDA, reliability, deciles, beeswarm, waterfall | Solid |
| ipywidgets | Section 6 live rescoring of one account on the same pipeline | Prototype, not a deployed app |
| joblib | Listed. No saved `.pkl` is committed (`.gitignore` excludes `models/`) | Mention only if you actually persist the pipeline |
| Jupyter | The analysis notebook | Strong |

### Tools listed or implied, with no artifact

| Tool | Status |
| --- | --- |
| imbalanced-learn | Pinned in `requirements.txt`. Code comment and notebook both refuse SMOTE. That refusal is the experience. |
| Streamlit | Pinned. No `app/` and no `streamlit` import. The conclusions say "promote `champion_pipeline` into `app/`." That is a next step. |
| Plotly | Pinned. Figures in the repo are matplotlib. |
| Excel, Power Query, PivotTables | No workbook in the tree. Treat as a study gap. |
| SQL / PostgreSQL | No `.sql` file. Treat as a study gap. You can still write the churn questions in SQL from the CSV schema. |
| PySpark, Spark SQL | Absent. |
| Deep learning, GNN, SciML | Absent. |

### Statistical methods you actually applied

| Method | Concrete use | What you may claim |
| --- | --- | --- |
| Base rate and class ratio | 26.5% churn, 2.8:1, weight 2.77 | You can define a no-skill PR-AUC (it equals the positive rate). |
| Stratified sampling | 80/20 split and 4-fold CV both stratified on `Churn` | You know why an unstratified split can move a 26.5% rate by chance. |
| Pearson correlation | Numeric leakage screen and the §3 matrix. tenure × TotalCharges = 0.83. ChargeRatio × MonthlyCharges = −0.04. ChargeRatio × Churn ≈ 0.026 | You can explain why a low correlation with the label is not "useless" once the feature is a ratio the tree can split. |
| Chi-square statistic and bias-corrected Cramér's V | `_chi2_stat` and `_cramers_v` in `src/data_pipeline.py`, flag if association > 0.9 | You implemented the association, including the bias correction. You did **not** report a p-value or degrees of freedom. |
| Quantile binning | `pd.qcut` on the descending rank for deciles. Calibration uses `strategy="quantile"` | You can explain why equal-count bins matter when scores are skewed. |
| Threshold metrics | Precision, recall, F1 sweep from 0.05 to 0.95 | You can say F1 treats FP and FN as equal, and your costs do not ($50 vs a year of bill). |
| Ranking metrics | ROC-AUC and PR-AUC (average precision) | You can say why PR-AUC moved your decision and ROC-AUC did not. |
| Proper scoring / calibration | Brier 0.162 vs 0.195. Reliability diagram. Mean predicted 40.8% vs 26.5% | You can separate discrimination from calibration. |
| Lift and capture | Decile churn rates, cumulative capture, top-k | This is your best "statistics in a business sentence." |
| Scenario arithmetic | Exposure and ROI with stated assumptions | This is decision analysis. It is not a confidence interval. |
| Single-row intervention on features | `what_if_simulator` | You can score a counterfactual **input**. You cannot call it a treatment effect. The README says so. |

Methods named in the references that you cited but did not fit: Platt scaling and isotonic regression (Niculescu-Mizil & Caruana, 2005). You know when you would add them. You did not add them.

---

## 2. Core technical sections

Each section has the concepts, questions with answers in your voice, one exercise with a solution, and the failure modes that show up in interviews.

---

### 2.1 Advanced Excel

**Status: Gap.** Nothing in the repo is an `.xlsx`. Study this until you can rebuild three artifacts you already trust: the contract rate table, the decile lift table, and the campaign cards.

#### Concepts to master

- **Lookup.** `XLOOKUP` (and `INDEX`/`MATCH` when a shop is still on older Excel). Exact match for IDs. `XLOOKUP` with `if_not_found`. Two-way lookups with `INDEX`/`MATCH`/`MATCH`.
- **Conditional aggregation.** `SUMIFS`, `COUNTIFS`, `AVERAGEIFS`, `MAXIFS`. These are the Excel version of `WHERE` plus `GROUP BY`.
- **PivotTables.** Rows, columns, values, filters. Show values as % of column, % of parent, running total. Group numeric tenure into bins. A pivot cache goes stale until you refresh.
- **Cleaning.** `TEXT`, `VALUE`, `TRIM`, `CLEAN`, `LEFT`/`RIGHT`/`MID`, `TEXTSPLIT` / Text to Columns, Flash Fill, Remove Duplicates, and **Power Query** (`Get Data`) for the steps you would otherwise redo by hand: change type, replace blank `TotalCharges`, fill the 11 tenure-0 rows with 0, drop `customerID`, add `ChargeRatio`.
- **Tables.** Format as Table (`Ctrl+T`). Structured references (`ChurnData[MonthlyCharges]`) so formulas survive new rows.
- **What-if.** Data tables (two-way) for save rate × cost per contact. Goal Seek for the break-even save rate. Solver only if you are optimizing under constraints.
- **Dashboards.** One page, three questions, slicers on `Contract` and `InternetService`. Do not plot every column. Match the briefing: who to call, who is High, what dollars sit behind the flag.
- **Power Pivot / Data Model.** Relationships and DAX (`CALCULATE`, `DIVIDE`, `SUMX`) once the grain is "one row per customer" joined to a contract dimension. Optional until SQL is solid.

#### Questions and answers

**Q1. Walk me through cleaning the Telco file in Excel.**

> I would load the CSV with Power Query. `TotalCharges` arrives as text because 11 brand-new customers have a blank. I replace blanks with 0 and set the type to decimal, the same rule as `pd.to_numeric(..., errors="coerce").fillna(0)` in `data_processing.py`. I remove `customerID` before any pivot, because a unique ID will explode a pivot and can leak identity if someone later one-hot encodes it. I add `ChargeRatio = [MonthlyCharges] / ([TotalCharges] + 1)` as a custom column, and a tenure band with a conditional column at 12, 24, and 48 months. I load the result to the Data Model, then build pivots off that query so a refresh repeats the cleaning.

**Q2. Contract churn rates without a Python notebook.**

> Customer grain, one row each. Pivot: rows = `Contract`, values = count of customers and count of churn = Yes. A calculated field `Churn Rate = DIVIDE([Churners], [Customers])`. On the training slice that matches my notebook I expect month-to-month about 42.7%, one-year 11.1%, two-year 2.9%. I add a second values field, churners as % of column total, which is the "89% of leavers are month-to-month" cut. I label the pivot "training association," because the people on two-year plans already selected into that plan.

**Q3. How would you show the 282-person list versus the 491-person flag to a manager who lives in Excel?**

> Two measures off the scored table. `High Flag` is 1 when predicted probability ≥ 0.59. `Call List` is 1 when the rank of predicted probability is in the top 20% (`RANK` or a pivot grouped by percentile). Cards: count of call-list rows, sum of actual churners on that list, sum of `MonthlyCharges` × 12 on the flag. I would not multiply probability by bill. My reliability diagram says a score near 0.59 corresponds to about a 30% observed rate.

**Q4. VLOOKUP is failing. What do you check?**

> The lookup column is not the leftmost column, so I switch to `XLOOKUP` or `INDEX`/`MATCH`. The match is approximate because the last argument was omitted or set TRUE. Types differ (text "123" vs number 123). Extra spaces, fixed with `TRIM` in Power Query. The table expanded and the range did not, which is why the source should be a Table.

**Q5. A two-way data table for the campaign.**

> Row input: save rate from 5% to 50%. Column input: cost per contact from $10 to $100. Formula: `saved = 190 * save_rate * 64.09 * 12 - 282 * cost`. At $50 and 35% the cell shows about $37,043 net. The row where net crosses zero at $50 is a save rate near 10%. That table is the artifact I wish I had built next to Section 5.4.

#### Exercise

The scored holdout has 1,409 rows with columns `y_true`, `y_proba`, `MonthlyCharges`. In Excel, produce (a) decile 1's churn rate and (b) 12-month exposure at a 0.59 flag.

**Solution.**

1. `Rank = RANK(B2, $B$2:$B$1410, 0)` with ties broken by adding `ROW()/100000` so `qcut(..., duplicates)` behavior stays close to `rank(method="first")`.
2. `Decile = MATCH(rank, {1,142,283,...})` or `=CEILING(rank / 141, 1)` because 1,409 / 10 leaves deciles of 141 and one remainder. Check that decile sizes are 140 or 141. My Python `qcut` on `rank(method="first")` forces 10 near-equal bins. Decile 1 churn in the notebook is 107/141 = 75.9%. If your bin edges differ by one row, say so.
3. Exposure: `=SUMIFS(MonthlyCharges, proba, ">=0.59") * 12`. Target: 491 accounts, about $74.89 average, **$441,250**.

#### Pitfalls

- Refresh the pivot after Power Query changes. A stale cache has burned more presentations than a wrong formula.
- "% of total" and "% of parent row" answer different questions. The 42.7% is churners within a contract. The 89% is that contract's share of all churners.
- Averaging churn rates across contracts without weights hides that month-to-month is 55% of the base.
- Formatted dollars that are actually text will silently drop out of `SUM`.
- Do not put the predicted probability on a dashboard axis labeled "chance they leave" unless you have calibrated.

---

### 2.2 SQL and PostgreSQL

**Status: Gap as a file.** The schema below is real. Write these queries until you can do them on a whiteboard.

Assume:

```sql
CREATE TABLE customers (
  customer_id        text PRIMARY KEY,
  gender             text,
  senior_citizen     int,
  partner            text,
  dependents         text,
  tenure             int,
  phone_service      text,
  multiple_lines     text,
  internet_service   text,
  online_security    text,
  online_backup      text,
  device_protection  text,
  tech_support       text,
  streaming_tv       text,
  streaming_movies   text,
  contract           text,
  paperless_billing  text,
  payment_method     text,
  monthly_charges    numeric,
  total_charges      numeric,  -- NULL for the 11 tenure-0 rows
  churn              text      -- 'Yes' / 'No'
);
```

#### Concepts to master

- **Filters and aggregates.** `WHERE` before aggregation, `HAVING` after. `COUNT(*)` vs `COUNT(total_charges)` (the second drops the 11 nulls).
- **Joins.** Inner, left, anti-join (`WHERE right.key IS NULL`), and the fact that a join multiplies rows when the key is not unique. Your grain is one customer. A join to a payments table without aggregation will double-count charges.
- **UNION vs UNION ALL.** `ALL` keeps duplicates and is cheaper.
- **Subqueries vs CTEs.** CTEs for the leakage-style steps you want a reviewer to read top to bottom. Correlated subqueries when the inner query depends on the outer row. They are often the slow version of a window function.
- **Windows.** `OVER (PARTITION BY contract ORDER BY tenure)` with `RANK`, `DENSE_RANK`, `ROW_NUMBER`, `LAG`, `SUM() OVER`, `AVG() OVER`, and a frame `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.
- **Conditional aggregation.** `AVG( (churn = 'Yes')::int )` or `FILTER (WHERE churn = 'Yes')`.
- **NULLs.** `NULL = NULL` is unknown. Use `IS NULL`. `COALESCE(total_charges, 0)`.
- **Performance.** Filter early. Index the columns you join and the columns you filter (`contract`, `churn`). `EXPLAIN` and look for seq scans on large tables, nested loops over big inner tables, and row estimates that are wildly off (`ANALYZE`). Avoid `SELECT *` in production queries. A window over an unfiltered 100M-row table will spill to disk. Predicate pushdown matters more once you are in Spark SQL.
- **Analytics patterns.** Cohort retention, funnels, period-over-period with `LAG`, percentiles with `PERCENTILE_CONT`, and top-k per group with `ROW_NUMBER`.

#### Questions and answers

**Q1. Churn rate by contract, with share of all churners. Match my training-set story, conceptually.**

```sql
WITH labeled AS (
  SELECT
    contract,
    (churn = 'Yes')::int AS churned
  FROM customers
)
SELECT
  contract,
  COUNT(*) AS accounts,
  SUM(churned) AS churners,
  ROUND(AVG(churned)::numeric, 3) AS churn_rate,
  ROUND(SUM(churned)::numeric / SUM(SUM(churned)) OVER (), 3) AS share_of_churners
FROM labeled
GROUP BY contract
ORDER BY churn_rate DESC;
```

> On the full file I expect the same shape as the notebook's training slice: month-to-month far above the 26.5% base, two-year near 3%, and month-to-month holding the large majority of leavers. I would say "full file" or "training 5,634" out loud so I do not mix the two denominators. Training month-to-month was 42.7% on 3,102 accounts and 1,326 of 1,495 leavers.

**Q2. Engineer ChargeRatio and tenure band in SQL.**

```sql
SELECT
  customer_id,
  tenure,
  monthly_charges,
  COALESCE(total_charges, 0) AS total_charges,
  monthly_charges / (COALESCE(total_charges, 0) + 1) AS charge_ratio,
  CASE
    WHEN tenure <= 12 THEN '0-1-year'
    WHEN tenure <= 24 THEN '1-2-years'
    WHEN tenure <= 48 THEN '2-4-years'
    ELSE '4+-years'
  END AS tenure_bucket
FROM customers;
```

> The `+ 1` matches `data_processing.py` and keeps a zero-history customer from dividing by zero. Those 11 rows are new accounts, not missing bills in the middle of the file.

**Q3. Top 20% by a stored score, and capture rate. This is Section 5.2.**

```sql
WITH scored AS (
  SELECT
    customer_id,
    churned,          -- 1/0 from the holdout label
    y_proba,
    NTILE(5) OVER (ORDER BY y_proba DESC) AS band_20  -- 1 = top 20%
  FROM holdout_scores
)
SELECT
  COUNT(*) FILTER (WHERE band_20 = 1) AS n_targeted,
  SUM(churned) FILTER (WHERE band_20 = 1) AS captured,
  SUM(churned) AS total_churners,
  ROUND(
    SUM(churned) FILTER (WHERE band_20 = 1)::numeric / SUM(churned),
    3
  ) AS capture_rate
FROM scored;
```

> On my holdout that query returns 282 targeted if I use a rounded 20% instead of `NTILE` (1,409 × 0.2 = 281.8 → 282 via `ROW_NUMBER`). `NTILE(5)` on 1,409 gives bands of 281 and 282. I would mention that off-by-one. The published capture is **190 / 374 = 50.8%**.

**Q4. Why can a join inflate revenue at risk?**

> Exposure is `SUM(monthly_charges) * 12` at customer grain for scores ≥ 0.59. If I join a one-to-many ticket table and then sum `monthly_charges`, each extra ticket repeats the bill. I aggregate tickets to one row per customer first, or I sum the bill from the customer table and join the aggregates. My $441,250 figure is a sum at customer grain. I can defend it only if the query stays at that grain.

**Q5. Find customers with no add-on support, in SQL, the anti-pattern and the clean version.**

```sql
-- Clean: the columns already live on the customer
SELECT customer_id
FROM customers
WHERE tech_support = 'No'
  AND online_security = 'No'
  AND internet_service = 'Fiber optic'
  AND contract = 'Month-to-month';
```

> If support were a child table, the anti-join is `FROM customers c LEFT JOIN support s ON ... WHERE s.customer_id IS NULL`. `NOT IN (SELECT ... )` turns the whole predicate unknown if the subquery emits a NULL. I use `NOT EXISTS` for that reason.

**Q6. Make it fast.**

> On a table this size, nothing matters. The interview answer they want: index the filter and join columns, look at `EXPLAIN (ANALYZE, BUFFERS)`, avoid a function wrapped on the indexed column (`WHERE date(ts) = ...` will not use an index on `ts`), and pre-aggregate before the join. For a window that only needs the top 20%, I filter with a subquery on a quantile rather than sorting the entire history twice.

#### Exercise

Write a query that returns, for each contract, the median tenure of churners and of stayers. PostgreSQL has `PERCENTILE_CONT`.

**Solution.**

```sql
SELECT
  contract,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tenure)
    FILTER (WHERE churn = 'Yes') AS median_tenure_churners,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tenure)
    FILTER (WHERE churn = 'No') AS median_tenure_stayers
FROM customers
GROUP BY contract;
```

Overall, the notebook's training medians are 10 and 38 months. By contract they will differ. Say the denominator.

#### Pitfalls

- Mixing training-set rates (5,634) with full-file rates (7,043) in the same sentence.
- `AVG(monthly_charges)` of churners is not "revenue we will lose." My own write-up calls $441,250 exposure because it treats every flagged account as a leaver and freezes the bill for 12 months.
- `NTILE` vs `ROW_NUMBER` vs `RANK` disagree on ties. My Python path uses `rank(method="first")` so ties break by position.
- Integer division: `190 / 374` in some engines is 0. Cast to numeric.
- A CTE is an optimization fence in older PostgreSQL. If a plan is slow, try inlining it.

---

### 2.3 Python for data science

**Status: Strongest tool area.** Speak from `src/`, not from a generic pandas tutorial.

#### Concepts to master

- **Data structures.** Series alignment on index (a silent bug if two frames do not share an index). Copy vs view. `df.copy()` at the start of `clean_and_engineer_features` is intentional.
- **Missing data.** `to_numeric(errors="coerce")` then `fillna(0)` only because those blanks are tenure 0. Filling the median would invent a bill for a customer who has not been billed.
- **Groupby.** `groupby("decile").agg(...)`. Watch `observed=True` on categorical groupers (your cohort SHAP code sets it).
- **Pipelines.** Fit preprocessing on train only. `ColumnTransformer` with `StandardScaler` on numerics and `OneHotEncoder(handle_unknown="ignore", drop="if_binary")` on categoricals. The same object is cloned inside every model so the bake-off is fair.
- **Leakage in code.** Scaler fit on all rows. Target encoding fit on all rows. Feature selection using the test label. Optuna objective that scores `X_test`. Your search calls `cross_val_score` on `X_train` only.
- **Metrics API.** `predict_proba[:, 1]`, then a threshold. `average_precision_score` is PR-AUC. `roc_auc_score` is the other one. Do not call `accuracy_score` in this interview.
- **Visualization.** A chart needs a claim. Your decile chart's claim is "monotonic staircase, 75.9% down to 0.7%."
- **Style.** Small functions with docstrings, `RANDOM_STATE = 42`, no notebook-only logic that the app would need. Section 6 still duplicates some slider logic in the notebook. That is a fair "what I would refactor" point.

#### Questions and answers

**Q1. Why is the preprocessing inside the pipeline?**

> If I scale on the full frame, the test fold's mean and variance influence the training features. Inside `Pipeline`, `cross_val_score` clones the steps and fits the scaler on each training fold only. The three models in `get_baseline_models` share that pattern, so logistic at 0.635 versus untuned XGBoost at 0.602 is an estimator gap. I also `drop="if_binary"` so a two-level category does not show up as two perfectly collinear dummies. `handle_unknown="ignore"` keeps a new level at score time from crashing. All zeros in that row means "this level was not seen in train," which is the honest behavior.

**Q2. Explain ChargeRatio in one minute.**

> `MonthlyCharges / (TotalCharges + 1)`. It is high when the current bill is large relative to everything the customer has paid so far, which is exactly new customers on an expensive plan. It is almost uncorrelated with the raw bill, r = −0.04 on the training set, so it is not a rescaled `MonthlyCharges`. In TreeSHAP it takes 12% of top-15 mean absolute mass and raw monthly charge takes 7%. The leakage audit flagged it as id-like because a continuous ratio is nearly unique (96.4%). Association with churn is about 0.026, so I kept it.

**Q3. Why did logistic beat default XGBoost, and why did you still tune the tree?**

> On one stratified holdout, class-weighted logistic reached PR-AUC 0.635 with recall 0.791 at the default 0.5 cut. The forest was more precise and less sensitive. Untuned XGBoost was last at 0.602. I still tuned XGBoost because TreeSHAP is native on the booster and default trees were under-regularized. Optuna picked depth 4, 450 trees, `min_child_weight` 10, and strong gamma and L1/L2. Holdout PR-AUC moved to 0.658, which is 0.022 above logistic. If that gap had not closed, the honest model to ship would have been logistic. CV 0.674 is not the number I quote as performance.

**Q4. How do you keep a notebook and a future app from drifting?**

> Transformations that change columns live in `src/data_processing.py`. Split, audit, and the column transformer live in `src/data_pipeline.py`. Anything the app will call is imported, not retyped. The Section 6 widgets rebuild `TenureBucket`, `TotalServicesSubscribed`, `TotalCharges`, and `ChargeRatio` in the cell. I would move that rebuild into the same module before a Streamlit app, which is the step the conclusions already name and which this repo has not done.

**Q5. A subtle pandas bug you protected yourself against.**

> `what_if_simulator` copies the one-row frame before writing overrides. Service toggles also recompute `TotalServicesSubscribed`, because leaving the count stale would score a different customer than the one on the screen. `clean_and_engineer_features` copies on entry for the same reason.

#### Exercise

From memory, write the decile table function's core three lines and the capture definition.

**Solution.**

```python
df["decile"] = pd.qcut(
    df["y_proba"].rank(method="first", ascending=False),
    10,
    labels=False,
) + 1
# capture at 20%: n_targeted = round(n * 0.2); take argsort(-proba)[:n_targeted]
```

`method="first"` breaks ties by original order so every bin has a size. Without it, `qcut` can fail or produce unequal edges when many scores tie. On this holdout, decile 1 is 141 people, 107 churners, rate 75.9%, and the top two deciles capture 190/374.

#### Pitfalls

- Fitting the scaler, the one-hot encoder, or a target encoding before `train_test_split`.
- Tuning on the test set, then reporting that same test score as confirmation.
- Reading `predict` (0.5 cutoff) when the business rule is a ranking.
- `class_weight` changes the loss. It does not change the prior. Your mean predicted probability moved to 40.8% because of this. Say that before someone asks you to price `p × bill`.
- Importing `imblearn.over_sampling.SMOTE` because it is in `requirements.txt`. Your write-up rejects it. Be consistent.
- Chaining `inplace=True` and a slice. Prefer returning a new frame.

---

### 2.4 Statistical analysis and inference

**Status: Partial.** You compute rates, correlations, a chi-square *statistic*, and Cramér's V. You do not report standard errors, confidence intervals, p-values, or hypothesis tests. This is the highest-leverage study gap after SQL, because your rates are large enough that the tests will agree with you, and you should know that formally.

#### Concepts to master

- **Estimand first.** "Churn rate among month-to-month customers in the training snapshot" is a descriptive estimand. "The effect of forcing a two-year contract" is a causal estimand you do not have.
- **Sampling distribution.** A rate p̂ from n independent Bernoulli trials has variance p(1−p)/n. Your customers are one cross-section. The independence assumption is approximate.
- **Confidence interval for a proportion.** Wald interval p̂ ± 1.96 √(p̂(1−p̂)/n) is fine when np and n(1−p) are both large. Wilson is better near 0 and 1 (your 2.9% two-year rate).
- **Hypothesis tests you must be able to choose.**
  - One proportion vs a benchmark: z-test.
  - Two proportions: two-sample z-test or chi-square on the 2×2 table.
  - Two means: Welch t-test (do not assume equal variance).
  - Three or more means: ANOVA, then pairwise tests with a multiplicity correction.
  - Categorical association: chi-square or Fisher's exact when expected counts are small.
  - Paired before/after: paired t or Wilcoxon.
- **p-value.** The probability of a result at least this extreme if the null is true and the sampling model is right. It is not the probability the null is true. It is not the size of the effect.
- **Effect size.** Difference in rates, relative risk, odds ratio, Cohen's d, Cramér's V. Your month-to-month rate is 42.7% versus a 26.5% base, about 1.6×, and about 15× the two-year rate. Those ratios are the effect. A tiny p-value on 5,634 rows is cheap.
- **Assumptions.** Independence, the distribution the interval uses, expected cell counts for chi-square (rule of thumb: most expected cells ≥ 5), no fishing across dozens of unplanned cuts without saying you explored.
- **Multiple comparisons.** If you test contract, fiber, payment method, senior, gender, and six add-ons, some p-values will be small by chance. Pre-specify the contract comparison. Label the rest as exploratory. Your SHAP ranking is a useful confirmation set because you stated the contract / ChargeRatio / fiber story as hypotheses in the README before leaning on the model.

#### Questions and answers

**Q1. Put a confidence interval on the training month-to-month churn rate.**

> 1,326 churners out of 3,102 month-to-month accounts in the training set is 42.75%. Standard error = √(0.4275 × 0.5725 / 3102) ≈ 0.0089. A 95% Wald interval is 0.4275 ± 1.96 × 0.0089 ≈ **41.0% to 44.5%**. The two-year rate is 39/1,359 ≈ 2.87%, SE ≈ 0.45 pp, Wald interval about **2.0% to 3.8%**. Those intervals do not overlap. I would still refuse the sentence "moving everyone to two-year would cut churn to 3%," because contract is chosen, not assigned.

**Q2. Is the contract gap "significant"?**

> Build the 3×2 table of contract by churn on the training set: month-to-month 1,326 vs 1,776 stayed, one-year 130 vs 1,043, two-year 39 vs 1,320. Chi-square on that table will be enormous on 5,634 rows. I would report the rate difference and the interval, and mention chi-square only to show I know the test. Practical significance is already obvious: 89% of leavers sit on month-to-month. Statistical significance is not the scarce resource here.

**Q3. Your leakage audit uses Cramér's V. What is it?**

> For a contingency table, φ² = χ² / n. Bias-corrected Cramér's V adjusts φ², the row count, and the column count by the amount of chance association you expect in a finite sample, then takes a square root. It lives on roughly 0 to 1. I flag a feature when V or |Pearson r| exceeds 0.9, which is "this column is almost the label." `ChargeRatio` was flagged by a different rule, uniqueness above 95%, and its Pearson r with churn was about 0.026. I can derive χ² as Σ (O−E)²/E with E = row total × column total / n, which is what `_chi2_stat` does. I did not look up a p-value from that χ².

**Q4. What is a p-value, in the words you will use if they interrupt you?**

> If the null were true, and I repeated the sampling procedure, the p-value is how often I would see a statistic at least this far from the null. A p-value of 0.03 is not a 3% chance that there is no effect. With 7,043 rows, a 1 percentage-point difference in churn can be "significant" and still be useless to a retention team that can only call 282 people.

**Q5. Where is the independence assumption shaky in your project?**

> The file is one cross-section of accounts. People in the same household, or the same acquisition campaign, are not independent, and I have no household id once `customerID` is dropped. The intervals above treat each row as an independent Bernoulli trial. They are good enough to show the contract gap is not noise. They are not a survey-weighted population inference, and they are not a causal standard error.

#### Exercise

Compute a 95% Wald interval for overall churn, 1,869 / 7,043.

**Solution.**

p̂ = 1869/7043 ≈ 0.26537. SE = √(0.26537 × 0.73463 / 7043) ≈ 0.00526. Margin = 1.96 × 0.00526 ≈ 0.0103. Interval ≈ **25.5% to 27.6%**. Quote this if someone asks "how precise is 26.5%?" Then say the business comparison that matters is not this interval. It is the top-decile rate of 75.9% versus that base.

#### Pitfalls

- Reporting a p-value without the effect size and the sample size.
- Using a paired test on unpaired contract groups.
- Running a t-test on the binary churn flag. Churn is Bernoulli. Compare rates, or fit a logistic model. A t-test on a 0/1 variable is numerically close to a two-proportion z-test in large samples and still the wrong story to tell.
- Treating the training set and the test set as two independent samples you may pool for a "more significant" EDA result after you have already used the test set to pick the model.
- Saying "the correlation is significant" about r = −0.04. On 5,634 rows it might be. It is still almost no linear association, which is the point of that cell.

---

### 2.5 A/B testing

**Status: Gap as an experiment. Strong as a design critique of your own ROI slide.** You did not randomize anything. You recommended a pilot. That recommendation is the interview.

#### Concepts to master

- **Unit of randomization.** The customer. If many lines share a household and you only randomize lines, interference makes the estimate optimistic. You do not have household ids here.
- **Hypothesis and estimand.** Example: among customers the model places in the current top 20%, a contract-upgrade offer increases 90-day retention relative to no outbound offer.
- **Metric hierarchy.** Primary: incremental retention (or incremental gross margin) at a fixed horizon. Guardrails: complaint rate, discount cost, offer acceptance, average bill of people who stay. Do not use PR-AUC as the experiment metric. The model is already frozen.
- **Control.** The right control for "does the call save people?" is eligible customers you do **not** call. Comparing called customers to historical churn labels is not an experiment. Your 1,869 churners have already left.
- **Sample size.** For two proportions, with baseline conversion p₁, minimum detectable effect δ, power 80%, two-sided α = 0.05:

  n per arm ≈ (z_{1−α/2} + z_{power})² × (p₁(1−p₁) + p₂(1−p₂)) / δ²

  z₀.₉₇₅ = 1.96, z₀.₈₀ = 0.84.

- **Peeking and sequential testing.** If you check every day and stop when p < 0.05, the false-positive rate climbs well above 5%. Use a fixed horizon, or a sequential method (group-sequential boundaries, or always-valid intervals such as mixture sequential probability ratio tests) if the business truly needs to stop early.
- **Interference, novelty, seasonality.** A retention offer in week 1 of a price change is not the offer in a quiet month. Run long enough to cover the billing cycle. Your horizon in the ROI sheet is 12 months. A pilot can use a shorter leading indicator, but you should say it is a proxy.
- **Segmenting after the fact.** Looking at fiber-only winners because the overall test was flat is a new hypothesis. Confirm it on the next pilot.

#### Questions and answers

**Q1. Design the pilot your notebook already asks for.**

> The 3.6× figure assumes a 35% save rate. The file cannot measure that, because the label is historical. I would freeze `champion_pipeline`, score customers who are still active, take a capacity-sized slice of the ranking, and randomly assign them to offer vs no offer. Primary metric: still active 90 days later, plus gross margin net of the $50 contact and any discount. I would pre-register the top-20% eligibility rule so I do not redraw the list after seeing results. I would not staff the 491-person flag just to enlarge the sample. Capacity belongs on the ranking.

**Q2. How big should the pilot be?**

> Suppose, inside the top 20%, the no-offer 90-day churn rate is 40% (retention 60%), and I want to detect a drop to 30% churn (a 10 point absolute save, which is my break-even neighborhood). p₁ = 0.60, p₂ = 0.70, δ = 0.10.

> n per arm ≈ (1.96 + 0.84)² × (0.6×0.4 + 0.7×0.3) / 0.10² = 7.84 × (0.24 + 0.21) / 0.01 = 7.84 × 45 = **353 per arm**, about **700** people.

> My published list is 282 on a 1,409-row holdout. A real base is larger than the test slice, but a 282-person one-arm "pilot" with no control cannot identify a 10-point effect. I would either widen eligibility, run longer and pool weeks, or accept that I can only detect a larger effect. I would say that out loud. It is a better answer than pretending 35% was measured.

**Q3. The model already picked who is risky. Is there still anything to randomize?**

> Yes. The model answers "who is high in the ranking." The experiment answers "does the offer change the outcome for those people." If I only call the top of the list and compare them to people lower in the list, I have confounded the offer with the risk score. Randomize **within** the eligible band.

**Q4. You peeked at week 2 and the save rate looks like 35%. Ship it?**

> No. Stopping because the result looks good inflates the win rate. I either wait for the planned 90 days or use a sequential boundary I set before the first call. The ROI sheet can be updated as a scenario. It does not become a measured 3.6× until the horizon completes.

**Q5. What would you do with a null result?**

> If the offer does not beat control by enough to clear the roughly 10% break-even save rate, I do not scale the 282-person motion. I keep the ranking for a different offer, because 50.8% capture says the list is enriched for leavers. Enrichment is not incremental lift. Those are different claims, and my README already separates them.

#### Exercise

Break-even save rate, from your own cards.

**Solution.**

Cost = 282 × 50 = 14,100. Value of one saved leaver at the full test-set mean bill = 64.09 × 12 = 769.08. Saved leavers needed = 14,100 / 769.08 ≈ 18.3. Those 18.3 must come from the 190 true leavers on the list (you correctly give no credit for the 92 stayers you also call). Break-even save rate = 18.3 / 190 ≈ **9.7%**, which you report as about 10%. If the pilot's confidence interval for the save rate lies entirely under 10%, the scenario's net benefit is not supported.

#### Pitfalls

- Using historical churners as the "treatment group." They are labels, not a cohort you can save.
- Changing the offer, the audience, and the creative in the same pilot. You will not know which one moved.
- Treating model precision (67.4% on the list) as a save rate.
- Ignoring cost in the primary metric and celebrating a retention bump that costs more than the retained bill.
- Sample-size formulas that use a one-sided test after you looked at the data and decided the direction.

---

### 2.6 ANOVA

**Status: Gap.** You never fit an ANOVA. You do have the right raw material: tenure and monthly charges across three contracts, and a binary churn label that should **not** be forced through ANOVA when a chi-square or a logistic regression is the direct model.

#### Concepts to master

- **One-way ANOVA.** Tests whether three or more group means share a common value. H₀: μ_month = μ_one = μ_two for, say, tenure. The statistic is between-group mean square over within-group mean square, compared with an F distribution on (k−1, N−k) degrees of freedom.
- **Assumptions.** Independent observations. Roughly normal residuals, which matters less at your sample size. Similar variances (Levene's test). When variances differ badly, Welch's ANOVA. When the outcome is skewed and you care about the median, Kruskal-Wallis.
- **Post-hoc.** A significant F says "somewhere the means differ." Tukey's HSD holds the family-wise error rate for all pairs. Bonferroni is simpler and more conservative. Dunnett's test if there is one control arm.
- **Two-way ANOVA.** Two factors, for example contract and internet service, plus an interaction. The interaction is the interesting line: the tenure gap by contract might be different for fiber than for no internet. Your cohort SHAP chart is the model version of "the story changes by segment." ANOVA would be the mean version.
- **Versus regression.** One-way ANOVA with k groups is linear regression on k−1 dummies. The F test matches the regression's overall F. Coefficients give you the contrasts directly, with the baseline group explicit. Logistic regression is the analogous move when the outcome is churn. That is why your baseline model is logistic, not an ANOVA on the 0/1 label.
- **Effect size.** η² = SS_between / SS_total. A tiny η² with a tiny p-value is a large-sample artifact.

#### Questions and answers

**Q1. When would you run ANOVA on this project?**

> To compare mean tenure, or mean monthly charges, across the three contracts. The business question "do contracts have different churn rates?" is a chi-square test or a logistic regression, because churn is binary. I already report those rates: 42.7%, 11.1%, 2.9% on the training set. ANOVA belongs on the continuous companions, where a t-test would only cover one pair and I have three groups.

**Q2. Sketch the one-way test on tenure.**

> Groups of size 3,102, 1,173, and 1,359 in the training set. Grand mean tenure, then between sum of squares Σ n_g (ȳ_g − ȳ)², within sum of squares Σ (y_i − ȳ_g)². F = (SSB / 2) / (SSW / 5631). I would not claim the result without computing it, but the medians already differ sharply for leavers versus stayers overall (10 vs 38), and month-to-month customers are the newer group. I expect a large F. I would follow with Tukey pairwise intervals and lead with the mean differences in months, not with the F statistic.

**Q3. Why not stop at the box plot of monthly charges?**

> The boxes overlap: stayers roughly span the same dollars as leavers, with a higher floor for leavers (median $80 vs $64). ANOVA on "leaver vs stayer" would flag the $16 mean gap and hide the overlap. For three contracts I would show the means with confidence intervals beside the ANOVA so a $5 gap on a $70 bill is not dressed up as a targeting rule. Fiber is inside that gap. A two-way model with contract and internet service keeps me from assigning the bill difference to the contract alone.

**Q4. ANOVA versus your logistic regression.**

> Logistic regression already includes contract as a category, with class weights, and it is judged on PR-AUC. ANOVA does not produce a ranking of customers. If the question is "which factor shifts the mean," ANOVA or OLS is the shorter path. If the question is "whom do we call," I stay with the classifier. I can still read contract's coefficient in the logistic model as the adjusted log-odds association, holding tenure and charges fixed. That adjustment is what the raw 15× rate ratio does not do.

#### Exercise

You have three group churn rates and you are tempted to ANOVA the 0/1 column. State the test you will run instead, and the first assumption you will check.

**Solution.**

Chi-square test of independence on the 3×2 table, or a logistic regression with contract dummies and a likelihood-ratio test against an intercept-only model. First check: expected cell counts. The smallest cell in the training table is 39 two-year churners. Expected counts will be well above 5 at this n, so the chi-square approximation is comfortable. Fisher's exact is unnecessary. Then report the rate differences, not only the p-value.

#### Pitfalls

- A significant ANOVA followed by uncorrected t-tests on every pair. The pairwise error rate is no longer 5%.
- Interpreting a contract main effect when the interaction with fiber is the real pattern.
- Using ANOVA language ("variance explained") to smuggle in a causal claim about forcing a two-year term.
- Forgetting that your observations are unbalanced (3,102 vs 1,173 vs 1,359). Type I and Type III sums of squares disagree once designs are unbalanced. In regression this is just "which terms are in the model when this coefficient is tested."

---

### 2.7 Regression

**Status: Strong on logistic as a baseline. Light on OLS diagnostics, because you never fit a linear model to a continuous target.** You do have the diagnostic story in disguise: collinearity between tenure and TotalCharges (r = 0.83), a class-weighted logistic loss, and a threshold that is not 0.5.

#### Concepts to master

- **Linear regression.** E[y|x] = β₀ + β₁x₁ + … Minimize squared error. Coefficient: the change in the mean of y for a one-unit change in x, holding the other regressors fixed. That "holding fixed" is statistical, not experimental.
- **Assumptions for inference on β.** Linearity in the parameters, independent errors, homoscedasticity, and roughly normal errors for small-sample t intervals. Random X versus fixed X is a modeling choice. Multicollinearity does not bias coefficients. It inflates their variance so signs and rankings get unstable.
- **Diagnostics.** Residual vs fitted (curve means the mean structure is wrong; a fan shape means variance changes). Q-Q plot. Cook's distance and leverage for the $118 bills and the tenure-0 rows. VIF for tenure, MonthlyCharges, and TotalCharges. A VIF above 5 or 10 says the shared variance is large. Your r = 0.83 is already that warning.
- **Logistic regression.** Model log-odds. Probability = 1 / (1 + e^{−z}). A coefficient of 0.5 on a dummy is an odds ratio of e^0.5 ≈ 1.65, **if** you did not also turn on `class_weight="balanced"`. With balanced weights, the intercept and the probability scale shift. Your Brier score and the 40.8% vs 26.5% gap are that shift, visible from the XGBoost side. The same phenomenon hits weighted logistic regression. Do not read a weighted model's `predict_proba` as a base-rate-correct chance without checking calibration.
- **Regularization.** L2 shrinks coefficients. L1 can zero them. Your champion's L1 and L2 were about 5.7 and 3.8, with gamma 3.9, on a depth-4 tree. That is the tree analogue of "I had 5,634 rows and I refused a deep fit."
- **Link to ANOVA and to trees.** Dummies for contract in OLS recover ANOVA. Trees can use tenure and TotalCharges together even when they move together. Your SHAP note says importance is shared, and TotalCharges falls to 3% of top-15 mass once tenure and the monthly rate are present. That is the collinearity showing up in a tree explanation.

#### Questions and answers

**Q1. Interpret a logistic result for this dataset without inventing a coefficient you did not publish.**

> I did not publish odds ratios. I published ranking quality. Class-weighted logistic regression reached holdout PR-AUC 0.635 and ROC-AUC 0.842, with recall 0.791 and precision 0.498 at the default 0.5 cutoff. The honest interpretation is: as a ranker it was the best untuned model, and at 0.5 it catches most leavers while being wrong about half the time. If I were asked for a coefficient story I would refit **without** class weights, or with weights and a calibration step, and then say "the month-to-month coefficient is an adjusted association on the log-odds scale, holding tenure, charges, and services fixed." I would not quote an uncalibrated probability as the chance a named customer leaves.

**Q2. Why keep both tenure and TotalCharges when r = 0.83?**

> For a linear model I would be cautious: the two coefficients would trade off and the standard errors would be wide. I might keep tenure and MonthlyCharges and drop TotalCharges, because TotalCharges is roughly rate × time. For XGBoost I kept all five numeric columns. Trees can split on either, and the later SHAP ranking shows TotalCharges doing little independent work (3% of top-15 mass). Keeping it did not create a leak. Dropping it would also have been defensible. I should be able to say that choice was pragmatic, not required.

**Q3. What does the intercept mean?**

> In an unweighted logistic model with dummy coding and scaled numerics, the intercept is the log-odds of churn when every numeric feature is at its train-set mean (because of `StandardScaler`) and every dropped baseline category is the one present. `drop="if_binary"` changes which level is the baseline for two-level fields. I would only interpret the intercept after checking the encoder's `categories_` and the scaler's means. I have not published that sentence because I never asked the logistic model to explain anyone. SHAP on the tree did that job.

**Q4. Diagnostics you would run if the target were monthly charges.**

> Residual plot against fitted values and against tenure. A curve would push me toward a spline or a log bill. A fan shape would push me toward `log(MonthlyCharges)` or robust standard errors. Influence of the handful of bills near $118. VIF among tenure, TotalCharges, and the service count (those correlations are 0.83, 0.74, 0.73, 0.65). Then I would still ask whether the decision needs a mean bill model at all. In this project the bill is an input and a weighting variable, not the target.

**Q5. Linear model vs your champion, in one sentence each.**

> Logistic regression is the interpretable, slightly weaker ranker (PR-AUC 0.635) and the one I would ship if the tuned tree had not cleared it. The tuned tree is the champion (0.658) because the gain survived the holdout and because TreeSHAP can decompose it. The tree will pick up threshold effects, such as the first-year tenure pile-up, without me writing the bins into the design matrix. `TenureBucket` is still in the features. That is partly redundant with raw tenure, and I kept both so the linear model and the plots could use the bins.

#### Exercise

You add an interaction: month-to-month × fiber. What changes in the story, and what must stay true in the code?

**Solution.**

The EDA already says leavers are enriched for fiber (70% vs 35%) and that month-to-month fiber is both expensive and easy to leave. An interaction lets the month-to-month log-odds differ for fiber versus DSL versus no internet. In the pipeline the interaction has to be created **before** the split's transformer is fit, or as a `FunctionTransformer` inside the pipeline, so the test fold does not use a definition learned from test rows. The holdout comparison must be redone. I would not claim the interaction matters unless PR-AUC or, better, top-20% capture actually moves. A coefficient can be nonzero and still leave the call list unchanged.

#### Pitfalls

- Reading `class_weight="balanced"` coefficients as if they came from a likelihood at the real 26.5% base rate.
- Quoting R² on the churn classifier. You are not fitting squared error on a continuous outcome. Your published scores are PR-AUC, ROC-AUC, precision, recall, F1, Brier.
- "Controlling for tenure" in a regression as a synonym for "the causal effect of contract." Tenure is a post-treatment companion of contract if people who hate the service both leave early and refuse a two-year term. Adjustment can still be useful as a descriptive stratification. It is not an experiment.
- Dropping a collinear variable and announcing the remaining coefficient "got more significant," as if that were new information rather than a reallocation of shared variance.

---

### 2.8 Machine learning fundamentals

**Status: Strong for supervised tabular classification, thresholding, calibration, and tree explanations. Absent: unsupervised projects, fraud, grid risk, PySpark, and GNN/SciML.** Answer those as knowledge. Do not adopt them as autobiography.

#### Concepts to master

- **Supervised vs unsupervised.** You have a label, `Churn`, known at training time, and the decision is taken later on people who have not yet left. That second part is why the file is a proxy. Clustering would be unsupervised. You did not ship a clustering. A fair aside: contract, tenure, and fiber already give you the segments a k-means would likely rediscover.
- **Bias and variance, in your search.** Untuned XGBoost (depth defaults, 300 trees) lost to a linear model. The search moved toward a shallow, heavily regularized tree and gained 0.056 PR-AUC on the holdout. That is a variance reduction story. If the holdout had landed far below the CV 0.674, you would call it overfit to the search. The gap you actually have is 0.674 CV vs 0.658 holdout, which you describe as the price of a real holdout.
- **Train, validation, test.** The 4-fold CV is the validation mechanism inside Optuna. The 1,409 rows are the test. You have **one** test cut. A senior interviewer will ask what you would do next: a second split, or nested CV, or a later time-based cohort. Your honest answer is in the limitations: all metrics are one 80/20 cut at `random_state=42`.
- **Metrics.**
  - Accuracy: rejected. Majority class is 73.5%.
  - ROC-AUC: probability a random leaver ranks above a random stayer. Yours is 0.850 for the champion. Can look strong while precision on the call list is what ops feels.
  - PR-AUC / average precision: area under precision vs recall. No-skill baseline equals the positive rate, **0.265**, not 0.5. Your champion is 0.658.
  - Precision, recall, F1 at a threshold. Your flag is 0.59, not 0.5.
  - Brier score: mean squared error of the probability. 0.162 vs 0.195 for a constant 26.5% prediction. Discrimination with miscalibration can still beat the constant and be unsafe to multiply by money.
  - Capture@k and lift: the metric that matches a 20% calling capacity.
- **Class imbalance.** 26.5% is real and not rare-event fraud. Weighting by 2.77 was enough. SMOTE would invent rows between customers and would make the reliability diagram harder to trust. Downsampling would throw away stayers and distort the bill distribution you later sum.
- **Feature engineering.** Ratios, bins, counts. One-hot with an unknown level policy. Scaling for the linear model. Trees do not need scaling. You scaled anyway because the **shared** preprocessor also serves logistic regression. That is a tradeoff: the tree sees scaled numerics, which is why the waterfall axis is in transformed units. You already wrote that caution.
- **Regularization and search.** Know your space: `n_estimators` 150–600 step 50, `max_depth` 2–8, `learning_rate` log-uniform 0.01–0.3, subsample and colsample 0.5–1, `min_child_weight` 1–10, `gamma` 0–5, `reg_alpha` and `reg_lambda` log-uniform 1e-3–10. TPE with seed 42. Thirty trials, best at trial 6, then a flat best-so-far line.
- **Calibration.** Reliability curve, quantile bins. Rank use vs probability use. Platt (logistic on the score) and isotonic (nonparametric, needs more data, can overfit) are the fixes you cited and did not apply.
- **Explanations.** SHAP values for a tree are an exact additive decomposition of the raw margin in your check (error 2.86e-06). Mean absolute SHAP is not a causal effect and not a probability. Cohorts can reorder the levers. Global importance said contract. The worst row said ChargeRatio first (+0.66) and month-to-month second (+0.46), from a base margin near 0.02 up to 2.96 (the 95.1% score).
- **Unsupervised, at interview depth.** k-means (scale first, k by silhouette or a business constraint, spherical clusters). Hierarchical clustering. PCA as a compression of correlated bill features, with the caveat that principal components are hard to offer a customer. You would rather keep ChargeRatio, which has a sentence.
- **Fraud, if they ask generally.** Rare positives (often under 1%), extreme class weights or focal loss, PR-AUC, dollar-weighted cost of false positives vs false negatives, concept drift, label delay, and leakage through "chargeback already filed" fields. You have **no** fraud project in this workspace. The transferable piece from churn is: pick the metric that matches the cost ratio, audit leakage, and do not read an uncalibrated score as a probability.
- **Big data, if they ask generally.** Your 7,043 rows do not need Spark. The point at which you would reach for PySpark is when the customer table no longer fits comfortably in memory or the joins against usage events are the bottleneck. The same split discipline applies: fit the pipeline on train partitions, and do not collect a global mean on the whole set before splitting. That is a knowledge answer, not a project you completed here.

#### Questions and answers

**Q1. Walk me through the model from business question to champion.**

> The question is whom a capacity-constrained retention team should contact, why, and what a campaign costs under stated assumptions. The data are IBM's public telco sample, 7,043 by 21. I drop `customerID`, fix 11 blank total charges, and add ChargeRatio, a tenure band, and a service count. I screen every column for id-like uniqueness and for association above 0.9. I stratified-split 80/20. I compare class-weighted logistic regression, a 300-tree forest, and XGBoost in one pipeline. Logistic leads at PR-AUC 0.635. I tune only XGBoost, on training folds, and the refit reaches 0.658 on the 1,409. I set a High flag at the F1 peak, 0.59, and I build the call list from the ranking, top 20%, which captures 190 of 374 leavers. I check calibration before anyone multiplies a score by money, and I check SHAP additivity before anyone reads a plot.

**Q2. Why PR-AUC rather than ROC-AUC?**

> ROC-AUC averages over all thresholds and can stay high when the positive class is the one you care about and you are still buried in false positives. PR-AUC uses precision, so the 26.5% base rate is the no-skill line. A useless ranker scores 0.265, not 0.5. Optuna maximized average precision for that reason. I still report ROC-AUC 0.850 so a reviewer can compare, and I do not select on it.

**Q3. Your scores over-call churn. Is the model wrong?**

> It is miscalibrated, and it still ranks. Mean predicted probability is 40.8% against a 26.5% outcome. The bin sitting on the 0.59 flag predicts about 58% and observes about 30%. Brier 0.162 still beats a constant 0.195, so the score contains information. Decile 1 observes 75.9% churn. I use the order for the call list and I sum actual bills behind the flag. I would fit Platt or isotonic on training folds before I ever priced an account as probability times bill. I would not retune the booster just to pretty the diagonal until that pricing use exists.

**Q4. How can SHAP be "exact" and still be the wrong slide for a CEO?**

> Exact means the parts add up to this model's raw margin, including the over-call from `scale_pos_weight`. It does not mean the parts are treatment effects. The CEO slide is the call list: 282 contacts, 190 leavers, 2.5× a random list of the same length, and a scenario that stays a scenario until a pilot measures the save rate. SHAP is the next slide, for the person who asks "what do we offer them?" The answer is contract first for month-to-month accounts, then bill-versus-history and fiber. People already on a two-year term are largely protected by that term. Gender and senior status are outside the top 15, so they are not the targeting rule.

**Q5. What would you improve in the model itself?**

> A time-based split if I had signup and churn dates. I do not. Nested validation or at least a second seed, because one `random_state=42` cut is thin. A cost-weighted threshold instead of F1, since a missed leaver and a wasted $50 contact are not equal. Calibration if probabilities get multiplied by money. Rebuild engineered fields inside `src/` before any app. Try the interaction of contract and fiber only if top-20% capture moves. Leave SMOTE off unless a rarer label shows up and I can show the reliability diagram still makes sense.

**Q6. Fraud question, answered honestly.**

> I have not shipped a fraud model in the work we are looking at. The pieces I would carry over are leakage audits, a precision-recall metric with the real base rate as the baseline, a cost matrix instead of F1, and a refusal to treat an uncalibrated score as a probability. Fraud would add label delay, a much smaller positive rate, and a stronger need to watch drift. I would not invent a fraud dataset to fill that sentence.

#### Exercise

Decile 1 has 107 churners out of 141. The base rate is 26.5% and there are 374 churners in the test set. Compute lift and the share of all churners in that decile.

**Solution.**

Churn rate = 107/141 ≈ 0.7589. Lift = 0.7589 / 0.265 ≈ **2.86×**. Share of churners = 107/374 ≈ **28.6%**. Two deciles reach 190/374 = **50.8%**. If an interviewer asks "is 2.86× good?", tie it to capacity: that enrichment is why a 20% budget captures about half of leavers, which is the 2.5× comparison against calling a random 20%.

#### Pitfalls

- Reporting the Optuna CV score (0.674) as the test score.
- Letting the default 0.5 cutoff into the business slide. Your operating points are 0.59 for the flag and top 20% for the list.
- Explaining a dummy-variable waterfall as if the axis were dollars or months. It is scaled features and 0/1 dummies.
- Claiming the what-if (95.1% → 69.3%) is the expected reduction in churn. It is a movement on an inflated score, and 69.3% is still above the flag. The simulator also does not raise `MonthlyCharges` when you add paid support, so the drop is an upper bound even on that score.
- Using SMOTE inside the pipeline after you have told the interviewer calibration matters.
- Describing 7,043 rows as a big-data system.

---

### 2.9 Data storytelling for non-technical stakeholders

**Status: Strong.** The README, the notebook's "what follows and why it matters" cells, and the briefing notes are a course in this. Study them as scripts.

#### Concepts to master

- **Lead with the decision.** The first screen of your README is the call list, the exposure, and the scenario. PR-AUC arrives later.
- **One chart, one sentence.** Deciles: risk is concentrated. Targeting bars: same headcount, 2.5× the leavers. SHAP bars: contract, then bill-versus-history, then fiber.
- **Separate three jobs.** Who to call (282). Who is marked High (491). What billing sits behind the flag ($441,250). Your table in the README is the template for any metric review.
- **Measured versus assumed.** 190 captured leavers are in the test labels. The 35% save rate is an input. Break-even near 10% tells a CFO how wrong the assumption can be before the surplus disappears.
- **Association versus action.** Two-year customers churn at 2.9% because they are two-year customers, newer customers are month-to-month, and fiber is tangled with price. The offer test on one row is a model probe.
- **Audience switch.** Analyst: PR-AUC 0.658, Brier 0.162, additivity 2.86e-06. Manager: half the leavers, one-fifth of the calls, do not budget 3.6× until the pilot. Agent on the phone: "high bill for how new you are, month-to-month, fiber, electronic check."
- **What you will not say.** You will not say the model is 85% accurate. You will not say 0.59 means a 59% chance. You will not say $441,250 will be lost. You will not say a two-year contract cuts churn to 3%.

#### Questions and answers

**Q1. Give the 60-second version.**

> On a held-out group of 1,409 customers, of whom 374 leave, calling the riskiest 282 people reaches 190 of those leavers. A random list of the same length would reach about 75. The list is about two-thirds people who do leave. I would spend the team's time there. A wider net of 491 people has about $441,000 of annual billing sitting behind it. That is the size of the exposure, not a forecast of the loss. A $50 offer that saved 35% of the true leavers on the list would net about $37,000 on this slice, a bit over 3.5 times the spend, and it still works if the save rate is only about 10%. I have not measured the save rate. That is the pilot.

**Q2. A VP says "just convert everyone to a two-year plan. Those customers barely leave."**

> People who already accepted a two-year plan leave at about 3%, and they are only 3% of leavers in the training data. People on month-to-month leave at about 43%, and they are 89% of leavers. The model agrees that contract is the strongest family of features. It does not tell us the 43% group would behave like the 3% group if we forced the contract. On the single highest-risk holdout account, switching the score's contract input to one year moves the model's number from 95% to about 82%, and adding support moves it to about 69%. That account is still above the flag, and those percentages sit on a scale I know runs hot. The right next step is to offer the term to a randomized slice of the call list and measure who is still here.

**Q3. "Why not call everyone the model marks High?"**

> High is 491 people, about a third of the holdout, at a precision of 56%. The team's actual constraint in the scenario is closer to 282 calls. Past the top of the ranking, each extra call picks up fewer leavers. By the bottom 40% of scores there are almost no leavers left, 6 out of 374. I would staff the ranked list and use the flag as a watchlist, not as a dialer queue.

**Q4. Explain SHAP to a retention lead who does not want a math lecture.**

> The model starts each person at a baseline and adds a push up or down for each fact it knows. For the riskiest person I looked at, the biggest upward pushes were a bill that is high for how little history they have, a month-to-month plan, and fiber. I checked that those pushes add back to the model's actual score for every one of the 1,409 people, so the chart is the model, not a second opinion. The pushes are reasons inside the model. They are not proof that changing the plan will save the account. That is why the script offers the term and then we measure.

#### Exercise

Rewrite the Brier sentence for a non-statistician, then the version for an interviewer who wants the term.

**Solution.**

Manager: "If I average the model's predicted chances, I get 41%. The real leave rate is 26%. So I will not quote the percentage on the screen as the chance they leave. I will use the ranking, which does put the true leavers at the top."

Interviewer: "Brier score is 0.162 against 0.195 for a constant forecast at the base rate, so the probabilities beat a naive forecast on squared error and are still shifted up by class weighting. Quantile calibration shows about a 29 percentage-point gap in the bin that contains the 0.59 threshold. I keep ranking and bill-sums, and I would calibrate before using the probability as a weight."

#### Pitfalls

- Opening with the algorithm name. XGBoost is a method. The call list is the product.
- A dashboard that shows 95.1% in a type size larger than the sentence about calibration.
- Letting a stakeholder multiply $441,250 by 35% in their head. Those denominators are different populations (491 flagged vs 190 captured leavers on the list of 282).
- Hiding the overlap in the bill box plot. Median $80 vs $64 is a shift, and the boxes still overlap, so "charge them less" is not a rule.

---

## 3. Project-based interview stories

No fraud, grid-risk, PySpark, or GNN project is in this workspace. Do not tell those stories. You have one deep project. Split it into three STARs so a loop of three interviewers does not hear the same paragraph. Numbers are the holdout numbers above.

### Story A — The metric was the product

**Situation.** A subscription telecom file, IBM's public sample of 7,043 customers, shows a 26.5% churn rate. The business pressure, which I framed from the usual industry range and a 4–5× acquisition-cost rule of thumb, is that saving a customer is cheaper than replacing one. I was explicit in the speaker notes that those industry multiples are context, not estimates from this file.

**Task.** Produce something a retention team can staff. A model that says "stay" for everyone is already 73.5% accurate and finds nobody.

**Actions.** I defined success as holdout PR-AUC, a chosen threshold, explanations that add up to the model, and a costed scenario on the same rows. I dropped `customerID`, repaired 11 blank `TotalCharges` on tenure-0 accounts, and added `ChargeRatio`, `TenureBucket`, and a six-service count. I screened features for identifier-like uniqueness and for association above 0.9 using Pearson and bias-corrected Cramér's V. I kept one `ColumnTransformer` inside every `Pipeline`. I handled the 2.8:1 mix with class weights (`scale_pos_weight` ≈ 2.77) and left SMOTE unused. I compared logistic regression, a random forest, and XGBoost. Logistic won the untuned round at PR-AUC 0.635. I then ran 30 Optuna trials on 4-fold PR-AUC, training data only. The search preferred a shallow regularized tree, depth 4 and 450 estimators. Refit on all 5,634 training rows, the holdout PR-AUC was 0.658 against logistic 0.635 and a no-skill line of 0.265.

**Result.** The model is a ranker with a measured capture rate: the top 20% of 1,409 holdout customers, 282 people, contains 190 of 374 leavers, precision 67.4%, 2.5× a random list of equal length. ROC-AUC is 0.850. I can defend why I do not lead with it.

**What I would improve.** A second split or nested CV. A cost-based threshold in place of F1. A time-based validation if dates existed.

### Story B — The score was not a probability, and the chart had to add up

**Situation.** Class weighting moved probability mass upward. A retention tool that prints "59%" will be read as a chance.

**Task.** Show whether the scores can be read as probabilities, and whether the explanations are the model or a second, looser story.

**Actions.** I binned the 1,409 scores into quantile bins and plotted predicted versus observed. I computed Brier score, 0.162, against 0.195 for always predicting 26.5%. Mean prediction was 40.8%. The worst bin predicted about 58% and observed about 30%, and that bin sits on the operating threshold. I set the High flag by sweeping thresholds and taking max F1, which landed at 0.59: precision 56.2%, recall 73.8%, 491 people, confusion matrix 276, 215, 98, 820. I told stakeholders F1 treats a false alarm and a miss as equal, while the campaign math does not, so 0.59 is a conservative proxy. Separately I built `TreeExplainer` on the booster after the preprocessor and checked that expected value plus SHAP equals the raw margin within 2.86e-06 on every holdout row.

**Result.** I can say precisely what the score is allowed to do. Order customers. Sum real bills behind the flag ($441,250). Do not say "0.59 means 59%," and do not multiply p by bill until a calibration layer exists. The explanation story matches the EDA: contract dummies are 29% of top-15 mean absolute SHAP, ChargeRatio 12%, fiber 10%. The worst account is local and specific: ChargeRatio pushes more than contract on that row. Cohort plots show that offering a longer contract to someone already on a two-year term aims at a feature that is already protecting them.

**What I would improve.** Report the logistic coefficients only after an unweighted or calibrated refit. Add Platt or isotonic on inner folds the day finance wants an expected-value price. Move the widget's feature rebuild into `src/` so the explanation path and the app path cannot diverge.

### Story C — Pricing a list without laundering the assumptions

**Situation.** A good ranker still gets misused. People multiply a probability by a bill, or they treat a scenario multiple as a promised ROI, or they try to call every positive prediction.

**Task.** Turn the holdout scores into three artifacts a manager can fund or reject: a queue, an exposure, and a campaign scenario whose assumptions are visible.

**Actions.** Deciles with `qcut` on a first-method rank. Top 20% via argsort. Exposure as the sum of `MonthlyCharges` for scores ≥ 0.59, times 12, with no probability weight. ROI charged to all 282 contacts at $50, and credited only for captured leavers times a 35% save rate times the **full test-set** mean bill of $64.09, not the richer $74.89 flagged mean. I also scored one real holdout row under a contract change and a support bundle, and I stated that the simulator does not increase the bill when support is added.

**Result.** Decile 1 churns at 75.9% (107/141). The top two deciles hold half the leavers. Campaign arithmetic: cost $14,100, revenue saved about $51,143, net about $37,043, multiple about 3.6×, break-even save rate about 10%. The what-if moves 95.1% to 81.5% to 69.3% and stays High. The briefing's recommended order is: pilot the list so 35% becomes a measurement, staff the list rather than the flag, then promote the same pipeline into an app.

**What I would improve.** The pilot design in Section 2.5 of this guide: randomize inside the eligible band, power it for about a 10-point retention effect, and refuse to call historical churn labels a treatment group. A two-way data table on save rate and contact cost belongs next to the slide so finance can move the assumptions without me in the room.

### If they ask for a second project

> The workspace I can walk through line by line is this churn analysis. I will not brief a fraud model, a grid-risk model, or a graph-neural-net paper as if it were mine unless we open that repository. I can talk about how the same discipline would transfer: freeze a metric that matches the decision, audit leakage, keep a baseline, and separate a score's rank from its probability.

### Likely rapid-fire follow-ups, with short answers

| Prompt | Answer |
| --- | --- |
| Why not accuracy? | Constant "No" is 73.5% and catches 0 leavers. |
| Why not SMOTE? | 26.5% is not that rare. Synthetic rows would muddy the calibration check I cared about. |
| Why is ChargeRatio not leakage? | Flagged for uniqueness, 96.4%. Correlation with churn ≈ 0.026. |
| Why is 0.674 not on the slide? | That is the best training CV. Holdout is 0.658. |
| Why did TotalCharges matter in EDA and not in SHAP? | It tracks tenure, r = 0.83. Once tenure and monthly price are in the tree, the lifetime sum adds about 3% of top-15 mass. |
| Is 3.6× real? | The capture is real. The multiple uses a $50 cost and a 35% save rate. Break-even is about 10%. |
| What is the no-skill PR-AUC? | The positive rate, 0.265. |
| Did you deploy? | No. The notebook rescores one row with ipywidgets. Streamlit is a dependency, and `app/` is a stated next step. |

---

## 4. Gap analysis and a 3-week study plan

### Gaps, in the order an interview loop will notice them

| Priority | Gap | Why it will come up | What "good enough" looks like |
| --- | --- | --- | --- |
| 1 | SQL, including windows and `EXPLAIN` | Almost every DS screen has a SQL round. You have zero `.sql` files. | Write the contract-rate, ChargeRatio, and top-20% capture queries in this guide from a blank editor in under 15 minutes. |
| 2 | Inference: intervals, tests, effect sizes | You quote 42.7% and 2.9% with no interval. A stats interviewer will ask. | Compute the Wald intervals in §2.4 without notes. Choose chi-square vs t vs ANOVA vs logistic for six spoken scenarios. |
| 3 | Experiment design | Your best slide depends on a save rate you did not measure. | Design the within-list pilot, including the sample-size arithmetic, and explain why peeking breaks it. |
| 4 | Excel under time pressure | Analyst loops still hand you a workbook. | Rebuild the contract pivot and the ROI data table from the CSV in under 30 minutes. |
| 5 | Regression diagnostics and odds ratios | You shipped logistic regression as a score and never read a coefficient. | Refit an **unweighted** logistic pipeline, print odds ratios for contract and fiber, and say what class weights would have done to them. |
| 6 | A second validation habit | One seed, one split. | Rerun the champion at two more seeds and report the range of PR-AUC and capture@20%. If you lack time to retrain Optuna, rerun the frozen hyperparameters. |
| 7 | Unsupervised and SQL-style product metrics | Not in the project. Common in screens. | One k-means or PCA notebook you can describe honestly as practice, plus a retention-cohort query. |
| 8 | Spark, fraud, GNN | Only if the job post lists them. | A one-page spoken boundary of what you have not done, plus the transferable leakage and metric rules. Do not fake a project. |

You do **not** need three weeks of generic XGBoost tutorials. The tree model is the part you can already defend.

### Week 1 — Make the missing fundamentals speak your project

**Days 1–2. SQL.** Load the CSV into PostgreSQL or SQLite. Write, in this order: churn rate by contract with share of churners, median tenure by contract and churn using `PERCENTILE_CONT` or a SQLite equivalent, `ChargeRatio` with `COALESCE`, top 20% capture with `ROW_NUMBER`, and exposure with a filter on a score table. Then `EXPLAIN` the capture query and describe one index you would add if the table grew to usage events. Redo the two queries you stumbled on the next morning.

**Days 3–4. Inference on numbers you already trust.** By hand or in a few lines of Python, interval for 1,869/7,043, interval for 1,326/3,102, interval for 39/1,359. Chi-square on the training contract table. Write five sentences that pair each interval with the causal caveat. Do ten "which test?" flash cards: binary vs continuous, two groups vs three, paired vs unpaired, rare cells vs large cells.

**Day 5. Experiments.** Derive the 353-per-arm figure in §2.5 from the formula without looking, then change δ from 10 points to 5 points and watch n quadruple, because δ is squared. Write the pilot protocol on one page: population, eligibility, assignment, primary metric, guardrails, horizon, sample size, peeking rule. This page becomes Story C's improvement paragraph.

**Days 6–7. Excel.** Power Query the raw CSV. Pivot contract rates. Two-way data table on save rate and contact cost that reproduces net ≈ $37,043 at 35% and $50. Say the refresh steps out loud.

### Week 2 — Deepen the model you already have

**Days 8–9. Logistic coefficients.** Refit `LogisticRegression` **without** `class_weight` inside the same preprocessor. Export odds ratios for the contract and internet dummies. Then refit the weighted version and put both reliability curves on one axis. The interview sentence writes itself: weighting helped recall in the bake-off and shifted the probability scale, which is why the champion's mean prediction is 40.8%.

**Day 10. Thresholds.** Replace F1 with a simple expected-cost sweep: cost of a false positive = $50, cost of a false negative = 12 × that row's `MonthlyCharges` (or the mean $64 if you want a single number). See whether the minimum-cost threshold sits below 0.59, as your notebook predicts. Bring the plot, not a new claimed optimum, unless you recompute it.

**Day 11. Stability.** Same hyperparameters, three seeds. Table of PR-AUC and capture@20%. If capture moves from, say, the high 40s to the low 50s, that range is what you quote. If you cannot run the fits, say the published numbers are one seed and that this is the check you owe.

**Day 12. Explanations under questioning.** Practice the waterfall from memory: base margin about 0.02, ChargeRatio +0.66, month-to-month +0.46, fiber +0.26, tenure +0.21, electronic check +0.17, total margin 2.96, probability 95.1%. Then the cohort punchline: do not offer a term upgrade to people whose term is already the protective feature.

**Days 13–14. Story reps.** Tell Story A, B, and C into a timer at 3 minutes and at 60 seconds. Record the 60-second version. Cut any sentence that starts with the library name.

### Week 3 — Interview reps and the holes that match the job post

**Days 15–16. Mixed screens.** Alternate one SQL prompt and one open "how would you measure this?" prompt. Good prompts: "retention by signup month," "second-highest bill per contract," "find customers with fiber and no support," "the PM changed the offer mid-test."

**Day 17. ANOVA and regression drills.** One-way ANOVA vocabulary on a tenure-by-contract question. Two-way interaction in one paragraph. VIF and the r = 0.83 pair. Odds ratio versus SHAP, and when you would show each.

**Day 18. Unsupervised, small and honest.** Standardize the numeric columns on the training set only. k-means with k from 2 to 6. If the segments line up with contract and fiber, say that the clusters recovered the EDA. If they do not, say that too. This is practice, and you will label it as practice.

**Days 19–20. Job-specific gap.** If the posting emphasizes product experiments, redo Week 1's pilot page and add a sequential-testing definition. If it emphasizes analytics engineering, spend the time on window functions and `EXPLAIN`. If it emphasizes ML, spend it on the seed-stability table and the cost-weighted threshold. If it emphasizes deep learning or graphs, prepare a clear boundary rather than a weekend crash course you might misrepresent.

**Day 21. Mock loop.** Hour 1: SQL. Hour 2: your project, with a hostile question on calibration and a hostile question on causality. Hour 3: a take-home style explanation of the three numbers 282, 190, and 10% break-even, written for a VP.

### Practice rules

- Every mock answer that uses a number must use a number from the locked table, or you say you are approximating.
- Every ROI sentence includes the save-rate assumption in the same breath.
- When you do not have a project, say what you would do and what you have already done that is analogous. The analogous work is this churn analysis.

---

## 5. Quick reference

### 5.1 SQL patterns

```sql
-- Rate and share of positives
SELECT contract,
       AVG((churn = 'Yes')::int) AS rate,
       SUM((churn = 'Yes')::int)::numeric
         / SUM(SUM((churn = 'Yes')::int)) OVER () AS share
FROM customers
GROUP BY contract;

-- Top k% with a deterministic tie break
SELECT * FROM (
  SELECT *,
         ROW_NUMBER() OVER (ORDER BY y_proba DESC, customer_id) AS rn,
         COUNT(*) OVER () AS n
  FROM scores
) s
WHERE rn <= ROUND(0.20 * n);

-- Running total inside a contract
SELECT customer_id, contract, tenure,
       SUM(monthly_charges) OVER (
         PARTITION BY contract ORDER BY tenure
         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS bill_so_far
FROM customers;

-- Anti-join
SELECT c.customer_id
FROM customers c
LEFT JOIN contacted x USING (customer_id)
WHERE x.customer_id IS NULL;

-- Previous value
LAG(churn_rate) OVER (ORDER BY month) 
-- Cohort: first month, then months since, then retention
-- Percentile
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tenure)
```

| Need | Pattern | Watch |
| --- | --- | --- |
| Filter before vs after aggregate | `WHERE` / `HAVING` | `HAVING` cannot see dropped rows |
| Keep unmatched parents | `LEFT JOIN` + `IS NULL` | `NOT IN` plus NULL |
| One row per group among many | `ROW_NUMBER() = 1` | `RANK` keeps ties |
| Share of total | `SUM() OVER ()` | Window happens after `GROUP BY` in the same select level only if you aggregated first. Use a subquery if unsure |
| Null bill | `COALESCE(total_charges, 0)` | `COUNT(col)` skips nulls |
| Speed | Index join/filter columns, `EXPLAIN` | Function on a column blocks a plain index |

### 5.2 Statistical decision tree

```text
What is the outcome?
├── Binary (churn, saved, clicked)
│   ├── One group vs a known rate → one-proportion z, Wilson interval if p is near 0 or 1
│   ├── Two groups, unpaired → two-proportion z or chi-square (2×2)
│   ├── Two groups, paired (same customer, before/after) → McNemar
│   ├── Three or more groups → chi-square, or logistic regression if you also adjust
│   └── A ranking or a probability, not a single rate
│       ├── Discrimination → ROC-AUC, PR-AUC (baseline = base rate)
│       └── Are the probabilities real? → calibration curve, Brier
├── Continuous (tenure, bill, revenue)
│   ├── Two groups → Welch t-test (medians: Mann-Whitney)
│   ├── Three or more → one-way ANOVA, Welch if variances differ
│   │     └── Which pairs? → Tukey HSD
│   ├── Two factors → two-way ANOVA, read the interaction first
│   └── Adjust for other columns → OLS, then residual plot, VIF, Cook's distance
└── Did we assign the treatment?
    ├── Yes, randomized → difference in the primary metric, with the sample size you planned
    └── No, customers chose the contract → association. Say so. Do not quote 2.9% as the effect of a forced term.
```

Effect size beside every p-value. With thousands of rows, "significant" is cheap. Your scarce resource is call capacity.

| Published comparison | Prefer |
| --- | --- |
| 42.7% vs 11.1% vs 2.9% churn | Rate difference and a chi-square or logistic likelihood-ratio test |
| Median tenure 10 vs 38 | Median difference. Means only if you are ready for skew |
| $80 vs $64 median bill | The overlap. A t-test will be "significant" and still a bad cutoff |
| tenure and TotalCharges, r = 0.83 | VIF / "shared variance," not a significance test on the correlation |
| Top decile 75.9% vs base 26.5% | Lift and capture, on the holdout, after the model was frozen |

### 5.3 Python patterns you already use

```python
# Target and split
y = df["Churn"].map({"Yes": 1, "No": 0})
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# Shared preprocessor, fit only inside the pipeline
pre = ColumnTransformer([
    ("numeric", StandardScaler(), numeric_features),
    ("categorical", OneHotEncoder(handle_unknown="ignore", drop="if_binary"),
     categorical_features),
])
pipe = Pipeline([
    ("preprocessor", pre),
    ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
])

# Imbalance weight for XGBoost
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()  # ≈ 2.77

# Ranking metrics, then a threshold that is not 0.5
proba = pipe.predict_proba(X_test)[:, 1]
pr_auc = average_precision_score(y_test, proba)   # no-skill = y_test.mean()
roc = roc_auc_score(y_test, proba)

# Top 20% capture
k = round(len(proba) * 0.20)
captured = y_test.to_numpy()[np.argsort(-proba)[:k]].sum()

# Deciles, highest risk = 1
decile = pd.qcut(pd.Series(proba).rank(method="first", ascending=False), 10, labels=False) + 1

# Calibration
brier = brier_score_loss(y_test, proba)
frac_pos, mean_pred = calibration_curve(y_test, proba, n_bins=10, strategy="quantile")
```

| Symptom | First place to look |
| --- | --- |
| Test score looks too good | Scaler or encoder fit before the split. Target leaked into a feature. Optuna saw the test fold |
| PR-AUC and the business disagree | You are thresholding at 0.5 or optimizing ROC |
| Probabilities all sit high | `class_weight` or `scale_pos_weight`. Check the reliability curve before multiplying by money |
| SHAP plot looks plausible and is wrong | Explainer received raw columns instead of preprocessor output. Run the additivity check |
| `qcut` complains about duplicate edges | Rank with `method="first"` before binning |
| App and notebook disagree on one customer | Engineered fields (`ChargeRatio`, service count) were not rebuilt with the slider |

### 5.4 Excel power-user sheet

| Task | Formula or gesture |
| --- | --- |
| Exact lookup, left or right | `=XLOOKUP(id, ids, values, "missing")` |
| Two-way lookup | `=INDEX(grid, MATCH(row, rows, 0), MATCH(col, cols, 0))` |
| Conditional sum | `=SUMIFS(bill, contract, "Month-to-month", churn, "Yes")` |
| Rate in a pivot | Value field → Count of churners / Count of customers, or DAX `DIVIDE` |
| Blank total charges | Power Query: replace blank, type = decimal. Equivalent of fill 0 |
| Ratio feature | `=[MonthlyCharges] / ([TotalCharges] + 1)` |
| Tenure band | `=IFS([@tenure]<=12,"0-1-year",[@tenure]<=24,"1-2-years",[@tenure]<=48,"2-4-years",TRUE,"4+-years")` |
| Rank for a call list | `=RANK([@score], [score], 0)` plus a tiny unique tie break |
| Scenario table | Data → What-If → Data Table. Row = save rate, column = cost |
| Break-even | Goal Seek: set net benefit to 0 by changing save rate. You should land near 10% at $50 |
| Freeze panes, named ranges | Freeze below the header. Name `SaveRate` and `CostPerContact` so the ROI formula reads in English |
| Shortcuts worth memorizing | `Ctrl+T` table, `Alt+N+V` pivot, `Ctrl+Shift+L` filter, `F4` cycle absolute references, `Ctrl+`` ` show formulas, `Alt+F1` chart from selection, `Ctrl+Alt+V` paste special |

Power Query steps for this file, in order: source CSV, set types, replace blank `TotalCharges`, drop `customerID`, add `ChargeRatio`, add tenure band, add service count from the six Yes/No columns, load to a Table. Pivots read that Table. A second query should not reimplement the cleaning.

---

## Follow-up prompts

Copy any of these into Cursor when you want to go deeper. They assume this guide and the churn repo stay open.

1. **SQL drill from my schema.** "Using `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv`, write a PostgreSQL script that loads the file, reproduces contract churn rates, median tenure by contract and churn, ChargeRatio, and a top-20% capture query. Then quiz me with five harder window-function variants and check my answers."

2. **Inference on my published rates.** "Compute Wilson and Wald intervals for every contract churn rate on both the full file and a stratified training split with `random_state=42`. Run the chi-square test. Then interview me: I have to explain each interval without implying that a two-year contract causes a 2.9% churn rate."

3. **Cost-weighted threshold and calibration.** "Refit the champion hyperparameters, sweep thresholds by expected cost using $50 per false positive and 12 × MonthlyCharges per false negative, and compare that cutoff to my F1 threshold of 0.59. Add a reliability curve and a note on whether Platt scaling changes the call list."

4. **Pilot design review.** "Design the randomized save-rate pilot for the top 20% list, with sample size, a primary metric, guardrails, and a no-peeking rule. Use my break-even save rate of about 10% as the effect I care about, and tell me where my 282-person holdout list is too small."

5. **Hostile mock on Story B.** "Interview me for 20 minutes as a skeptical hiring manager. Push on class weights versus SMOTE, the CV 0.674 versus holdout 0.658, SHAP versus causation, and the 95.1% to 69.3% what-if. Grade each answer against `docs/interview-study-guide.md` and quote the file I should have cited."
