"""
13-slide maroon briefing deck (PPTX + PDF).

Does not replace the 26-slide executive version.
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas as pdf_canvas

OUT_DIR = Path(__file__).resolve().parent
PPTX_PATH = OUT_DIR / "Beyond_Accuracy_Churn_Brief.pptx"
PDF_PATH = OUT_DIR / "Beyond_Accuracy_Churn_Brief.pdf"

SLIDE_W = 13.333
SLIDE_H = 7.5
TOTAL = 13

# Maroon family (ASU-adjacent)
MAROON_DARK = "#4A0E22"
MAROON = "#8C1D40"
MAROON_MID = "#6B1533"
GOLD = "#FFC627"
CREAM = "#F8F1E9"
INK = "#2A1218"
MUTED = "#6B4A52"
WHITE = "#FFFFFF"
CARD = "#F7F0F2"
LINE = "#E4D4D8"
SOFT = "#C4A4AE"


def rgb(hex_color: str) -> RGBColor:
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rl(hex_color: str) -> Color:
    return HexColor(hex_color)


def set_run(paragraph, text, size=18, bold=False, color=INK, name="Calibri"):
    paragraph.clear()
    run = paragraph.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = rgb(color)
    run.font.name = name
    return run


def add_rect(slide, x, y, w, h, fill, line=None, rounded=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(
        shape_type, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(0.75)
    if rounded:
        try:
            shape.adjustments[0] = 0.08
        except Exception:
            pass
    shape.shadow.inherit = False
    return shape


def add_box(slide, x, y, w, h, text, size=16, bold=False, color=INK,
            align=PP_ALIGN.LEFT, name="Calibri"):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    set_run(p, text, size=size, bold=bold, color=color, name=name)
    return box


def add_paras(slide, x, y, w, h, lines, size=15, color=INK, spacing=8, bold=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(spacing)
        set_run(p, line, size=size, bold=bold, color=color)
    return box


def add_footer(slide, page, section=""):
    add_rect(slide, 0, 7.28, SLIDE_W, 0.03, GOLD)
    add_box(slide, 0.45, 7.30, 9.0, 0.18,
            f"Beyond Accuracy  ·  Customer Churn{('  ·  ' + section) if section else ''}",
            size=10, color=MUTED)
    add_box(slide, 11.3, 7.30, 1.6, 0.18, f"{page}  /  {TOTAL}",
            size=10, color=MUTED, align=PP_ALIGN.RIGHT)


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def add_cards(slide, cards, y=1.40, h=1.32):
    n = len(cards)
    gap = 0.20
    left = 0.45
    width = (SLIDE_W - 0.9 - gap * (n - 1)) / n
    accents = [MAROON, MAROON_MID, GOLD, SOFT]
    for i, card in enumerate(cards):
        x = left + i * (width + gap)
        add_rect(slide, x, y, width, h, CARD, rounded=True)
        add_rect(slide, x, y, 0.08, h, accents[i % len(accents)])
        add_box(slide, x + 0.20, y + 0.12, width - 0.32, 0.22,
                card["label"].upper(), size=10, color=MUTED, bold=True)
        add_box(slide, x + 0.20, y + 0.38, width - 0.32, 0.42,
                card["value"], size=20, color=INK, bold=True)
        add_box(slide, x + 0.20, y + 0.86, width - 0.32, 0.36,
                card["hint"], size=11, color=MUTED)


def add_takeaway(slide, text, y=6.52):
    add_rect(slide, 0.45, y, 12.43, 0.60, MAROON_DARK, rounded=True)
    add_box(slide, 0.65, y + 0.14, 12.05, 0.36, text, size=13, color=WHITE)


def blank(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, WHITE)
    return slide


def heading(slide, title, subtitle=None):
    add_rect(slide, 0, 0, SLIDE_W, 0.10, MAROON)
    add_box(slide, 0.45, 0.28, 12.4, 0.48, title, size=24, color=MAROON, bold=True)
    if subtitle:
        add_box(slide, 0.45, 0.78, 12.4, 0.32, subtitle, size=14, color=MUTED)


def build_pptx() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)

    # 1 Cover ----------------------------------------------------------------
    s = blank(prs)
    add_rect(s, 0, 0, SLIDE_W, SLIDE_H, MAROON_DARK)
    add_rect(s, 0, 0, 0.22, SLIDE_H, GOLD)
    add_box(s, 0.75, 1.15, 12.0, 0.30,
            "ARIZONA STATE UNIVERSITY", size=13, color=GOLD, bold=True)
    add_box(s, 0.75, 1.85, 12.0, 1.3,
            "Beyond Accuracy", size=42, color=WHITE, bold=True)
    add_box(s, 0.75, 3.15, 11.6, 1.0,
            "A business-driven, interpretable machine learning approach\nto customer churn prediction",
            size=20, color=CREAM)
    add_rect(s, 0.75, 4.40, 2.4, 0.06, GOLD)
    add_box(s, 0.75, 4.70, 11.5, 0.40,
            "Sileshi Hirpa", size=22, color=WHITE, bold=True)
    add_box(s, 0.75, 5.20, 11.5, 0.35,
            "Business Analytics + Machine Learning", size=16, color=GOLD)
    add_box(s, 0.75, 5.60, 11.5, 0.35,
            "W. P. Carey School of Business  ·  Arizona State University",
            size=15, color=CREAM)
    add_box(s, 0.75, 6.55, 11.5, 0.30,
            "IBM Telco Customer Churn  ·  Held-out evaluation on 1,409 customers",
            size=12, color=SOFT)
    add_notes(s, "Name, major, school on the cover. Title is the argument: accuracy is not the finish line.")

    # 2 Contents + dataset ---------------------------------------------------
    s = blank(prs)
    heading(s, "Contents and dataset",
            "What this briefing covers, and the data it is built on.")
    items = [
        ("01", "Problem and method", "Why accuracy fails, and the three guardrails."),
        ("02", "EDA and implications", "Tenure, contract, price — and what that means now."),
        ("03", "Model and SHAP", "Why XGBoost ships, and why each customer is High."),
        ("04", "Applications", "Call list, exposure, campaign, live dashboard."),
        ("05", "Close", "Conclusions and an ordered recommendation."),
    ]
    for i, (num, title, blurb) in enumerate(items):
        y = 1.25 + i * 0.72
        add_rect(s, 0.45, y, 6.20, 0.64, CARD, rounded=True)
        add_box(s, 0.62, y + 0.08, 0.7, 0.45, num, size=16, color=MAROON, bold=True)
        add_box(s, 1.35, y + 0.06, 5.1, 0.28, title, size=14, color=INK, bold=True)
        add_box(s, 1.35, y + 0.32, 5.1, 0.26, blurb, size=11, color=MUTED)

    add_rect(s, 6.90, 1.25, 5.95, 5.15, CARD, rounded=True)
    add_rect(s, 6.90, 1.25, 5.95, 0.10, GOLD)
    add_box(s, 7.15, 1.50, 5.5, 0.35, "Dataset", size=16, color=MAROON, bold=True)
    add_paras(s, 7.15, 1.95, 5.5, 4.2, [
        "IBM Telco Customer Churn.",
        "7,043 subscribers. 21 raw fields: demographics, tenure, services, contract, billing, and the churn label.",
        "Annual churn in this file is 26.5% — typical of subscription telecom.",
        "80/20 stratified split: 5,634 train, 1,409 holdout (374 leavers). Both stay at 26.5%.",
        "Citation: IBM. Telco Customer Churn. Public sample dataset. Local copy: data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv.",
    ], size=13, spacing=7)
    add_footer(s, 2, "Overview")
    add_notes(s, "Cite IBM on this slide. Do not claim the file is a current production extract.")

    # 3 Problem --------------------------------------------------------------
    s = blank(prs)
    heading(s, "Problem statement",
            "Churn is expensive. Accuracy is the wrong score for it.")
    add_cards(s, [
        {"label": "Base rate", "value": "26.5%",
         "hint": "1,495 leavers in training"},
        {"label": "Always-“No” accuracy", "value": "73.5%",
         "hint": "Catches zero at-risk accounts"},
        {"label": "Replacement cost", "value": "4–5×",
         "hint": "Acquire vs retain, industry rule"},
    ], y=1.25)
    add_paras(s, 0.55, 2.85, 12.2, 3.3, [
        "The practical question is not only “will this customer leave?” It is which accounts are worth an intervention, what that costs, and what it saves.",
        "A model that predicts “stay” for everyone is already 73.5% accurate and useless to a retention desk.",
        "Objective: rank the base by risk, explain why each person is High in terms a team can act on, and price a campaign on the same holdout rows.",
        "Success is PR-AUC on unseen data, a deliberate threshold, SHAP that adds back to the model, and a costed case with replaceable assumptions.",
    ], size=15, spacing=8)
    add_takeaway(s, "Takeaway: Optimize ranking and capture, not accuracy. The output is a call list.")
    add_footer(s, 3, "Problem")
    add_notes(s, "Industry 20–30% churn and 4–5× acquisition cost are the business frame, not estimates from this file.")

    # 4 Methodology ----------------------------------------------------------
    s = blank(prs)
    heading(s, "Methodology",
            "CRISP-DM. Three non-negotiables before any model is trusted.")
    rows = [
        ("01", "Leakage screen first",
         "Every feature is checked for identifier-like uniqueness and suspiciously strong target association before it enters a model. ChargeRatio looks unique (96.4%) — a false positive (r ≈ 0.026)."),
        ("02", "One shared pipeline",
         "StandardScaler + one-hot in a single ColumnTransformer, fit only on train. All three candidates see the same features, so the bake-off is the estimator, not the prep."),
        ("03", "Weights, not SMOTE",
         "class_weight / scale_pos_weight ≈ 2.77. Train on the real 2.8:1 mix. Synthetic rows would distort the later calibration check."),
        ("04", "Holdout, then explain",
         "Tune with 4-fold Optuna on train only. Score 1,409 unseen rows. TreeSHAP on the fitted classifier. Business numbers use that same test set."),
    ]
    for i, (num, title, body) in enumerate(rows):
        y = 1.22 + i * 1.22
        add_rect(s, 0.45, y, 12.43, 1.10, CARD, rounded=True)
        add_rect(s, 0.45, y, 0.10, 1.10, GOLD if i % 2 == 0 else MAROON)
        add_box(s, 0.75, y + 0.14, 0.7, 0.32, num, size=14, color=MAROON, bold=True)
        add_box(s, 1.50, y + 0.14, 11.0, 0.32, title, size=16, color=INK, bold=True)
        add_box(s, 1.50, y + 0.50, 11.0, 0.48, body, size=13, color=MUTED)
    add_footer(s, 4, "Method")
    add_notes(s, "Engineered features: ChargeRatio, TenureBucket, TotalServicesSubscribed. customerID dropped.")

    # 5 EDA ------------------------------------------------------------------
    s = blank(prs)
    heading(s, "Exploratory analysis",
            "Training set (5,634). The data already ranks risk before a model is fit.")
    add_cards(s, [
        {"label": "Median tenure", "value": "10 vs 38 mo",
         "hint": "Leavers vs stayers  ·  55% leave by month 12"},
        {"label": "Month-to-month churn", "value": "42.7%",
         "hint": "1.6× base  ·  89% of all leavers"},
        {"label": "Median bill gap", "value": "+$16 / mo",
         "hint": "$80 vs $64  ·  boxes still overlap"},
        {"label": "ChargeRatio × bill", "value": "r = −0.04",
         "hint": "A different axis from raw dollars"},
    ], y=1.22)
    add_paras(s, 0.55, 2.80, 12.2, 3.3, [
        "Leavers leave early. 822 of 1,495 training leavers sit at or before month 12. That is a snapshot, not a proof that waiting 38 months would have saved them.",
        "Contract is how easy it is to leave: month-to-month 42.7%, one-year 11.1%, two-year 2.9%. Month-to-month is 55% of the base and 89% of the people who left.",
        "Leavers pay more, but a “high bill” cutoff would also flag many stayers. 70% of leavers are on fiber vs 35% of stayers.",
        "ChargeRatio (monthly bill / accumulated history) is almost uncorrelated with MonthlyCharges. SHAP later ranks it above the raw bill.",
    ], size=14, spacing=7)
    add_takeaway(s, "Takeaway: New, month-to-month, premium-vs-history. Those are the three raw patterns the model has to recover.")
    add_footer(s, 5, "EDA")
    add_notes(s, "Use 55% (822/1,495), not the earlier 53% draft. Contract rates are training-set rates.")

    # 6 Implications ---------------------------------------------------------
    s = blank(prs)
    heading(s, "Insight, interpretation, and today’s business",
            "What a retention team should do with those patterns — and what they should not.")
    rows = [
        ("Insight",
         "Risk concentrates where switching costs are thin: the first year, a flexible contract, and a bill that is high relative to history — often fiber."),
        ("Interpretation",
         "This is association, not a conversion experiment. The two-year rate of 2.9% describes people who already chose a term, not the effect of forcing one."),
        ("Implication now",
         "In a high-churn subscription market, capacity is scarce. Spend the first call-hour on new month-to-month fiber, not on a demographic rule. Gender and senior status never enter the later top-15 SHAP list."),
        ("What not to do",
         "Do not cut price from the $16 gap alone. Fiber and contract sit inside that box plot. Do not treat “switch everyone to two-year” as a forecasted 29% drop."),
    ]
    for i, (title, body) in enumerate(rows):
        y = 1.22 + i * 1.22
        add_rect(s, 0.45, y, 12.43, 1.10, CARD, rounded=True)
        add_rect(s, 0.45, y, 0.10, 1.10, MAROON)
        add_box(s, 0.75, y + 0.16, 11.8, 0.30, title, size=16, color=MAROON, bold=True)
        add_box(s, 0.75, y + 0.50, 11.8, 0.48, body, size=14, color=INK)
    add_footer(s, 6, "EDA")
    add_notes(s, "Today: acquisition still costs more than retention; month-to-month and digital checkout make leaving cheap. Target friction, not a demographic.")

    # 7 Model selection ------------------------------------------------------
    s = blank(prs)
    heading(s, "Model selection and the deployment rule",
            "Same preprocessor. Same weights. Tuning had to beat logistic or we ship logistic.")
    add_cards(s, [
        {"label": "Logistic  ·  test PR-AUC", "value": "0.635",
         "hint": "First before tuning"},
        {"label": "XGBoost untuned", "value": "0.602",
         "hint": "Why defaults do not ship"},
        {"label": "XGBoost tuned", "value": "0.658",
         "hint": "+0.022 vs logistic  ·  ROC-AUC 0.850"},
        {"label": "High / Low flag", "value": "0.59",
         "hint": "F1-max  ·  491 of 1,409  ·  not a chance"},
    ], y=1.22)
    add_paras(s, 0.55, 2.80, 12.2, 3.3, [
        "Optuna (30 trials, 4-fold on train) picked a shallow, regularized tree (depth 4, 450 estimators). CV peak 0.674; holdout 0.658 is the number that counts.",
        "At 0.59: precision 56.2%, recall 73.8%, F1 0.638. Confusion: 276 / 215 / 98 / 820. That flag sizes exposure. It is not the call list.",
        "Scores over-call: mean predicted 40.8% vs 26.5% observed. Worst bin (on the flag) is 58% predicted vs 30% observed. Do not say “0.59 means 59%.”",
        "Deploy the ranking for who to call. Deploy 0.59 only as High / Low. Do not multiply p × bill until the scores are recalibrated.",
    ], size=14, spacing=7)
    add_takeaway(s, "Takeaway: Champion = tuned XGBoost. Staff the ranking. Use 0.59 to mark High, not to quote a probability.")
    add_footer(s, 7, "Model")
    add_notes(s, "F1 treats FP and FN as equal. A cost-weighted cutoff would sit lower. 0.59 is conservative.")

    # 8 SHAP -----------------------------------------------------------------
    s = blank(prs)
    heading(s, "Interpretation with SHAP",
            "Additivity holds to 2.86e-06 on all 1,409 rows. Exact decomposition of this model, including the over-call.")
    add_cards(s, [
        {"label": "Month-to-month", "value": "21%",
         "hint": "Largest single bar  ·  mean |SHAP| 0.565"},
        {"label": "All contract dummies", "value": "29%",
         "hint": "Month-to-month + two-year"},
        {"label": "ChargeRatio", "value": "12%",
         "hint": "Outranks raw MonthlyCharges (7%)"},
        {"label": "Fiber optic", "value": "10%",
         "hint": "Next service lever"},
    ], y=1.22)
    add_paras(s, 0.55, 2.80, 12.2, 3.3, [
        "Those four features are 51% of top-15 SHAP mass. Gender and senior status do not appear. The company can pull contract, price-to-history, and service mix.",
        "Unsigned bars answer how much. Direction is in the beeswarm: month-to-month and high ChargeRatio raise risk; long tenure and a two-year term lower it.",
        "Worst holdout row (1-month fiber, $95.10, no support): ChargeRatio outruns contract locally. What-if: 95.1% → 81.5% (one-year) → 69.3% (+ Tech Support and Online Security). Still High vs 0.59.",
        "SHAP explains the model. It is not a causal treatment effect. Already-on-term customers are protected by the term; “offer a contract” only fits month-to-month.",
    ], size=14, spacing=7)
    add_takeaway(s, "Takeaway: Contract first, then bill-vs-history, then fiber. Necessary on the worst row. Not sufficient to clear 0.59.")
    add_footer(s, 8, "SHAP")
    add_notes(s, "Units are raw margin. 4.4 over-call remains. Direction of the what-if is usable; the levels are high.")

    # 9 Applications ---------------------------------------------------------
    s = blank(prs)
    heading(s, "Applications: list, exposure, campaign",
            "Same 1,409 holdout customers. Three jobs. Do not mix the numbers.")
    add_rect(s, 0.45, 1.22, 4.00, 4.95, CARD, rounded=True)
    add_rect(s, 0.45, 1.22, 4.00, 0.10, GOLD)
    add_box(s, 0.65, 1.48, 3.6, 0.28, "CALL LIST", size=12, color=MAROON, bold=True)
    add_box(s, 0.65, 1.85, 3.6, 0.45, "282 people", size=26, color=INK, bold=True)
    add_paras(s, 0.65, 2.45, 3.6, 3.4, [
        "Top 20% of the ranking.",
        "190 of 374 leavers.",
        "50.8% capture · 67.4% precision.",
        "2.5× a random 20% list.",
        "Who gets called this month.",
    ], size=13, spacing=6)

    add_rect(s, 4.65, 1.22, 4.00, 4.95, CARD, rounded=True)
    add_rect(s, 4.65, 1.22, 4.00, 0.10, MAROON)
    add_box(s, 4.85, 1.48, 3.6, 0.28, "FLAG  ·  0.59", size=12, color=MAROON, bold=True)
    add_box(s, 4.85, 1.85, 3.6, 0.45, "491 people", size=26, color=INK, bold=True)
    add_paras(s, 4.85, 2.45, 3.6, 3.4, [
        "Everyone at or above 0.59.",
        "276 leavers · 215 false alarms.",
        "Average bill $74.89.",
        "$441,250 of 12-month billing.",
        "Exposure. Never p × bill.",
    ], size=13, spacing=6)

    add_rect(s, 8.85, 1.22, 4.03, 4.95, CARD, rounded=True)
    add_rect(s, 8.85, 1.22, 4.03, 0.10, GOLD)
    add_box(s, 9.05, 1.48, 3.6, 0.28, "CAMPAIGN ON THE 282", size=12, color=MAROON, bold=True)
    add_box(s, 9.05, 1.85, 3.6, 0.45, "3.6× scenario", size=24, color=INK, bold=True)
    add_paras(s, 9.05, 2.45, 3.6, 3.4, [
        "Cost $14,100 (282 × $50).",
        "Saved $51,143 · net $37,043.",
        "35% save rate, $64.09 bill, 12 mo.",
        "Break-even save rate ≈ 10%.",
        "Replace 35% with a pilot.",
    ], size=13, spacing=6)
    add_footer(s, 9, "Applications")
    add_notes(s, "190 captured leavers are measured. 35% is not. Price the 282, not the $441k pool.")

    # 10 Dashboard -----------------------------------------------------------
    s = blank(prs)
    heading(s, "Dashboarding",
            "Section 6: the same champion_pipeline, on live controls. No refit. No mock-up.")
    add_cards(s, [
        {"label": "Who is scored", "value": "One account",
         "hint": "Same worst-row profile as the waterfall"},
        {"label": "High / Low line", "value": "0.59",
         "hint": "The flag, not a promise they leave"},
        {"label": "What sliders rebuild", "value": "3 fields",
         "hint": "TenureBucket, TotalCharges, ChargeRatio"},
        {"label": "What stays fixed", "value": "The rest",
         "hint": "Payment method and other add-ons"},
    ], y=1.22)
    add_paras(s, 0.55, 2.80, 12.2, 3.3, [
        "Each click overwrites contract, internet, tenure, monthly bill, Tech Support, and Online Security, then rebuilds the engineered fields so they stay consistent with the sliders.",
        "Replaying the what-if (one-year, then support + security) should land near 81.5% then 69.3% — still High. Tenure, two-year, and internet are extra levers that cell did not freeze.",
        "A manager uses the dashboard to test an offer on a named account. A retention lead uses the 282-person list to staff the week. Those are different screens.",
        "Promotion path: move champion_pipeline into app/ with these controls as the UI. Do not retune from the notebook.",
    ], size=14, spacing=7)
    add_takeaway(s, "Takeaway: Dashboard = local what-if. List = who to call. Flag = who is High. Three surfaces, one model.")
    add_footer(s, 10, "Dashboard")
    add_notes(s, "Clicks do not rescore on drag — click Score customer. Levels remain inflated from 4.4.")

    # 11 Conclusion ----------------------------------------------------------
    s = blank(prs)
    heading(s, "Conclusion",
            "The useful output is a ranked, explainable, costed list — not a leaderboard score.")
    add_cards(s, [
        {"label": "Holdout capture", "value": "50.8%",
         "hint": "190 of 374 leavers in 282 contacts"},
        {"label": "Vs a random 20%", "value": "2.5×",
         "hint": "Same headcount, no model"},
        {"label": "Champion PR-AUC", "value": "0.658",
         "hint": "Beats logistic 0.635 and no-skill 0.265"},
        {"label": "What is not measured", "value": "35% save",
         "hint": "The 3.6× multiple waits on a pilot"},
    ], y=1.22)
    add_paras(s, 0.55, 2.80, 12.2, 3.3, [
        "The model recovers the EDA: contract, ChargeRatio, and fiber drive the score. That is actionable. Demographics are not.",
        "Two numbers must stay apart. 282 is who to call. 491 / $441,250 is exposure behind the 0.59 flag — not a loss forecast, and never p × bill.",
        "SHAP and the what-if move this model, including its over-call (mean predicted 40.8%). They do not prove a causal treatment effect.",
        "All of this is one 80/20 split at random_state=42, on one public snapshot. It answers who is at risk now, not whether risk is rising.",
    ], size=14, spacing=7)
    add_takeaway(s, "Takeaway: Rank, explain, price. Then measure the save rate before anyone budgets 3.6×.")
    add_footer(s, 11, "Close")
    add_notes(s, "Close the argument here. Next slide is the ordered ask.")

    # 12 Recommendations -----------------------------------------------------
    s = blank(prs)
    heading(s, "Recommendations",
            "Do these in order. Do not start with a dashboard redesign.")
    steps = [
        ("1", "Pilot the 282",
         "Hold out a slice so the 35% save rate becomes a measured one. Until that number exists, treat 3.6× as a scenario, not a budget. Break-even is about 10%."),
        ("2", "Staff the list, watch the flag",
         "Capacity follows the ranking (282). 0.59 marks High and sizes the $441,250 pool. Go deeper only if the pilot actually saves people."),
        ("3", "Offer contract first, then support",
         "Month-to-month is the lever that matches SHAP and EDA. Already-on-term accounts need price or service, not another term. Do not promise the worst row will fall below 0.59."),
        ("4", "Promote the pipeline",
         "Move champion_pipeline into app/ with the Section 6 controls. Revisit 0.59 only after monthly capacity is known. Recalibrate only if you start pricing p × bill × 12."),
    ]
    for i, (num, title, body) in enumerate(steps):
        y = 1.20 + i * 1.35
        add_rect(s, 0.45, y, 12.43, 1.22, CARD, rounded=True)
        add_rect(s, 0.45, y, 1.05, 1.22, MAROON_DARK)
        add_box(s, 0.45, y + 0.38, 1.05, 0.45, num, size=26, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
        add_box(s, 1.75, y + 0.16, 10.8, 0.32, title, size=16, color=INK, bold=True)
        add_box(s, 1.75, y + 0.52, 10.8, 0.55, body, size=13, color=MUTED)
    add_footer(s, 12, "Close")
    add_notes(s, "If asked about isotonic: only when they price individual accounts as p × bill. Not before.")

    # 13 Close / sources -----------------------------------------------------
    s = blank(prs)
    add_rect(s, 0, 0, SLIDE_W, SLIDE_H, MAROON_DARK)
    add_rect(s, 0, 0, 0.22, SLIDE_H, GOLD)
    add_box(s, 0.75, 0.85, 12.0, 0.35,
            "SOURCES AND CONTACT", size=13, color=GOLD, bold=True)
    add_box(s, 0.75, 1.35, 12.0, 0.55,
            "Staff the list. Watch the flag. Measure the save rate.",
            size=22, color=WHITE, bold=True)
    add_notes(s, "Leave this up. Contact is on the cover.")
    add_box(s, 0.75, 2.15, 11.8, 3.5,
            "IBM. Telco Customer Churn. Public sample, 7,043 customers / 21 features.\n"
            "Chapman et al. (2000). CRISP-DM 1.0.\n"
            "Chen & Guestrin (2016). XGBoost. KDD.   ·   Akiba et al. (2019). Optuna. KDD.\n"
            "Lundberg & Lee (2017). Interpreting model predictions. NeurIPS. (SHAP)\n"
            "Niculescu-Mizil & Caruana (2005). Predicting good probabilities. ICML.\n"
            "Code: src/data_pipeline.py, modeling.py, interpretability.py, business_impact.py.\n"
            "Holdout: 1,409 customers  ·  random_state=42  ·  champion = Optuna-tuned XGBoost.",
            size=14, color=CREAM)

    add_box(s, 0.75, 5.90, 11.8, 0.35,
            "Sileshi Hirpa  ·  Business Analytics + Machine Learning",
            size=15, color=WHITE, bold=True)
    add_box(s, 0.75, 6.30, 11.8, 0.30,
            "W. P. Carey School of Business  ·  Arizona State University",
            size=14, color=GOLD)
    add_box(s, 0.75, 6.70, 11.8, 0.28,
            "hirpast@gmail.com  ·  linkedin.com/in/sileshi-hirpa  ·  hirpadata.com",
            size=13, color=SOFT)

    assert len(prs.slides) == TOTAL, len(prs.slides)
    return prs


def draw_pdf():
    c = pdf_canvas.Canvas(str(PDF_PATH), pagesize=(SLIDE_W * 72, SLIDE_H * 72))
    W, H = SLIDE_W * 72, SLIDE_H * 72

    def rect(x, y, w, h, fill, radius=0):
        c.setFillColor(rl(fill))
        if radius:
            c.roundRect(x * 72, H - (y + h) * 72, w * 72, h * 72, radius * 72, fill=1, stroke=0)
        else:
            c.rect(x * 72, H - (y + h) * 72, w * 72, h * 72, fill=1, stroke=0)

    def text(x, y, msg, size=16, bold=False, color=INK, align="left", max_w=None):
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.setFillColor(rl(color))
        px, py = x * 72, H - y * 72 - size
        if max_w:
            lines = simpleSplit(msg, font, size, max_w * 72)
            for i, line in enumerate(lines):
                yy = py - i * (size + 3)
                if align == "center":
                    c.drawCentredString(px, yy, line)
                elif align == "right":
                    c.drawRightString(px, yy, line)
                else:
                    c.drawString(px, yy, line)
            return
        if align == "center":
            c.drawCentredString(px, py, msg)
        elif align == "right":
            c.drawRightString(px, py, msg)
        else:
            c.drawString(px, py, msg)

    def footer(page, section=""):
        rect(0, 7.28, SLIDE_W, 0.03, GOLD)
        text(0.45, 7.48, f"Beyond Accuracy  ·  Customer Churn{('  ·  ' + section) if section else ''}",
             size=9, color=MUTED)
        text(12.9, 7.48, f"{page}  /  {TOTAL}", size=9, color=MUTED, align="right")

    def cards(items, y=1.40, h=1.32):
        n = len(items)
        gap = 0.20
        width = (SLIDE_W - 0.9 - gap * (n - 1)) / n
        accents = [MAROON, MAROON_MID, GOLD, SOFT]
        for i, card in enumerate(items):
            x = 0.45 + i * (width + gap)
            rect(x, y, width, h, CARD, radius=0.07)
            rect(x, y, 0.08, h, accents[i % 4])
            text(x + 0.20, y + 0.28, card["label"].upper(), size=8, bold=True, color=MUTED)
            text(x + 0.20, y + 0.68, card["value"], size=15, bold=True, color=INK, max_w=width - 0.35)
            text(x + 0.20, y + 1.08, card["hint"], size=8, color=MUTED, max_w=width - 0.35)

    def takeaway(msg):
        rect(0.45, 6.52, 12.43, 0.58, MAROON_DARK, radius=0.06)
        text(0.65, 6.88, msg, size=11, color=WHITE, max_w=12.0)

    def bullets(lines, y, size=12, leading=0.36):
        for i, line in enumerate(lines):
            text(0.55, y + i * leading, line, size=size, color=INK, max_w=12.2)

    def light_head(title, subtitle):
        rect(0, 0, SLIDE_W, SLIDE_H, WHITE)
        rect(0, 0, SLIDE_W, 0.10, MAROON)
        text(0.45, 0.55, title, size=20, bold=True, color=MAROON, max_w=12.4)
        text(0.45, 0.95, subtitle, size=11, color=MUTED, max_w=12.4)

    # 1
    rect(0, 0, SLIDE_W, SLIDE_H, MAROON_DARK)
    rect(0, 0, 0.22, SLIDE_H, GOLD)
    text(0.75, 1.40, "ARIZONA STATE UNIVERSITY", size=12, bold=True, color=GOLD)
    text(0.75, 2.25, "Beyond Accuracy", size=38, bold=True, color=WHITE)
    text(0.75, 3.20, "A business-driven, interpretable machine learning approach",
         size=15, color=CREAM, max_w=11.6)
    text(0.75, 3.55, "to customer churn prediction", size=15, color=CREAM)
    rect(0.75, 4.40, 2.4, 0.05, GOLD)
    text(0.75, 4.95, "Sileshi Hirpa", size=20, bold=True, color=WHITE)
    text(0.75, 5.40, "Business Analytics + Machine Learning", size=13, color=GOLD)
    text(0.75, 5.80, "W. P. Carey School of Business  ·  Arizona State University",
         size=12, color=CREAM)
    text(0.75, 6.70, "IBM Telco Customer Churn  ·  Held-out evaluation on 1,409 customers",
         size=11, color=SOFT)
    c.showPage()

    # 2
    light_head("Contents and dataset", "What this briefing covers, and the data it is built on.")
    items = [
        ("01", "Problem and method", "Why accuracy fails, and the three guardrails."),
        ("02", "EDA and implications", "Tenure, contract, price — and what that means now."),
        ("03", "Model and SHAP", "Why XGBoost ships, and why each customer is High."),
        ("04", "Applications", "Call list, exposure, campaign, live dashboard."),
        ("05", "Close", "Conclusions and an ordered recommendation."),
    ]
    for i, (num, title, blurb) in enumerate(items):
        y = 1.25 + i * 0.72
        rect(0.45, y, 6.20, 0.64, CARD, radius=0.06)
        text(0.62, y + 0.40, num, size=13, bold=True, color=MAROON)
        text(1.35, y + 0.28, title, size=12, bold=True, color=INK)
        text(1.35, y + 0.50, blurb, size=9, color=MUTED)
    rect(6.90, 1.25, 5.95, 5.15, CARD, radius=0.07)
    rect(6.90, 1.25, 5.95, 0.10, GOLD)
    text(7.15, 1.70, "Dataset", size=14, bold=True, color=MAROON)
    for i, line in enumerate([
        "IBM Telco Customer Churn.",
        "7,043 subscribers. 21 raw fields: demographics, tenure, services, contract, billing, and the churn label.",
        "Annual churn in this file is 26.5% — typical of subscription telecom.",
        "80/20 stratified split: 5,634 train, 1,409 holdout (374 leavers). Both stay at 26.5%.",
        "Citation: IBM. Telco Customer Churn. Public sample dataset. Local copy: data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv.",
    ]):
        text(7.15, 2.15 + i * 0.72, line, size=10, color=INK, max_w=5.5)
    footer(2, "Overview")
    c.showPage()

    # 3
    light_head("Problem statement", "Churn is expensive. Accuracy is the wrong score for it.")
    cards([
        {"label": "Base rate", "value": "26.5%", "hint": "1,495 leavers in training"},
        {"label": "Always-“No” accuracy", "value": "73.5%", "hint": "Catches zero at-risk accounts"},
        {"label": "Replacement cost", "value": "4–5×", "hint": "Acquire vs retain, industry rule"},
    ], y=1.25)
    bullets([
        "The question is which accounts are worth an intervention, what it costs, and what it saves.",
        "A model that predicts “stay” for everyone is already 73.5% accurate and useless to a desk.",
        "Objective: rank the base, explain why each person is High, and price a campaign on the holdout.",
        "Success: PR-AUC on unseen data, a deliberate threshold, SHAP that adds up, replaceable assumptions.",
    ], y=2.90)
    takeaway("Takeaway: Optimize ranking and capture, not accuracy. The output is a call list.")
    footer(3, "Problem")
    c.showPage()

    # 4
    light_head("Methodology", "CRISP-DM. Three non-negotiables before any model is trusted.")
    rows = [
        ("01", "Leakage screen first",
         "Identifier-like uniqueness and strong target association are checked first. ChargeRatio looks unique (96.4%) — a false positive (r ≈ 0.026)."),
        ("02", "One shared pipeline",
         "StandardScaler + one-hot, fit only on train. The bake-off is the estimator, not the prep."),
        ("03", "Weights, not SMOTE",
         "scale_pos_weight ≈ 2.77. Train on the real 2.8:1 mix so calibration is not built on fake rows."),
        ("04", "Holdout, then explain",
         "Optuna on train only. Score 1,409 unseen rows. TreeSHAP on the fitted classifier. Business numbers use that test set."),
    ]
    for i, (num, title, body) in enumerate(rows):
        y = 1.22 + i * 1.22
        rect(0.45, y, 12.43, 1.10, CARD, radius=0.06)
        rect(0.45, y, 0.10, 1.10, GOLD if i % 2 == 0 else MAROON)
        text(0.75, y + 0.38, num, size=12, bold=True, color=MAROON)
        text(1.50, y + 0.38, title, size=13, bold=True, color=INK)
        text(1.50, y + 0.75, body, size=11, color=MUTED, max_w=11.0)
    footer(4, "Method")
    c.showPage()

    # 5
    light_head("Exploratory analysis", "Training set (5,634). The data already ranks risk before a model is fit.")
    cards([
        {"label": "Median tenure", "value": "10 vs 38 mo", "hint": "Leavers vs stayers  ·  55% leave by month 12"},
        {"label": "Month-to-month churn", "value": "42.7%", "hint": "1.6× base  ·  89% of all leavers"},
        {"label": "Median bill gap", "value": "+$16 / mo", "hint": "$80 vs $64  ·  boxes still overlap"},
        {"label": "ChargeRatio × bill", "value": "r = −0.04", "hint": "A different axis from raw dollars"},
    ], y=1.22)
    bullets([
        "822 of 1,495 training leavers sit at or before month 12. Snapshot, not a survival proof.",
        "Contract: 42.7% / 11.1% / 2.9%. Month-to-month is 55% of the base and 89% of leavers.",
        "Leavers pay more, but a high-bill cutoff flags many stayers. 70% of leavers are on fiber.",
        "ChargeRatio later outranks raw MonthlyCharges in SHAP (12% vs 7% of top-15 mass).",
    ], y=2.85)
    takeaway("Takeaway: New, month-to-month, premium-vs-history. Those are the three patterns the model must recover.")
    footer(5, "EDA")
    c.showPage()

    # 6
    light_head("Insight, interpretation, and today’s business",
               "What a retention team should do with those patterns — and what they should not.")
    blocks = [
        ("Insight",
         "Risk concentrates where switching costs are thin: first year, flexible contract, bill high versus history — often fiber."),
        ("Interpretation",
         "Association, not a conversion experiment. The 2.9% two-year rate describes people who already chose a term."),
        ("Implication now",
         "Capacity is scarce. Spend the first call-hour on new month-to-month fiber, not on a demographic rule."),
        ("What not to do",
         "Do not cut price from the $16 gap alone. Do not read “switch everyone to two-year” as a 29% forecast."),
    ]
    for i, (title, body) in enumerate(blocks):
        y = 1.22 + i * 1.22
        rect(0.45, y, 12.43, 1.10, CARD, radius=0.06)
        rect(0.45, y, 0.10, 1.10, MAROON)
        text(0.75, y + 0.38, title, size=13, bold=True, color=MAROON)
        text(0.75, y + 0.75, body, size=12, color=INK, max_w=11.8)
    footer(6, "EDA")
    c.showPage()

    # 7
    light_head("Model selection and the deployment rule",
               "Same preprocessor. Same weights. Tuning had to beat logistic or we ship logistic.")
    cards([
        {"label": "Logistic  ·  test PR-AUC", "value": "0.635", "hint": "First before tuning"},
        {"label": "XGBoost untuned", "value": "0.602", "hint": "Why defaults do not ship"},
        {"label": "XGBoost tuned", "value": "0.658", "hint": "+0.022 vs logistic  ·  ROC-AUC 0.850"},
        {"label": "High / Low flag", "value": "0.59", "hint": "F1-max  ·  491 of 1,409  ·  not a chance"},
    ], y=1.22)
    bullets([
        "Optuna picked a shallow regularized tree. CV 0.674; holdout 0.658 is the number that counts.",
        "At 0.59: 56.2% precision, 73.8% recall, F1 0.638. The flag sizes exposure. It is not the call list.",
        "Mean predicted 40.8% vs 26.5% observed. Do not say “0.59 means 59%.”",
        "Deploy the ranking for who to call. Deploy 0.59 only as High / Low.",
    ], y=2.85)
    takeaway("Takeaway: Champion = tuned XGBoost. Staff the ranking. Use 0.59 to mark High, not to quote a probability.")
    footer(7, "Model")
    c.showPage()

    # 8
    light_head("Interpretation with SHAP",
               "Additivity holds to 2.86e-06 on all 1,409 rows. Exact decomposition of this model.")
    cards([
        {"label": "Month-to-month", "value": "21%", "hint": "Largest bar  ·  mean |SHAP| 0.565"},
        {"label": "All contract dummies", "value": "29%", "hint": "Month-to-month + two-year"},
        {"label": "ChargeRatio", "value": "12%", "hint": "Outranks raw MonthlyCharges (7%)"},
        {"label": "Fiber optic", "value": "10%", "hint": "Next service lever"},
    ], y=1.22)
    bullets([
        "Those four features are 51% of top-15 mass. Gender and senior status do not appear.",
        "Worst row (1-month fiber, $95.10): 95.1% → 81.5% (one-year) → 69.3% (+ support). Still High.",
        "SHAP explains the model, including the over-call. It is not a causal treatment effect.",
        "“Offer a contract” only fits month-to-month. Already-on-term accounts need a different lever.",
    ], y=2.85)
    takeaway("Takeaway: Contract first, then bill-vs-history, then fiber. Necessary on the worst row. Not sufficient.")
    footer(8, "SHAP")
    c.showPage()

    # 9
    light_head("Applications: list, exposure, campaign",
               "Same 1,409 holdout customers. Three jobs. Do not mix the numbers.")
    cols = [
        (0.45, GOLD, "CALL LIST", "282 people",
         ["Top 20% of the ranking.", "190 of 374 leavers.", "50.8% capture · 67.4% precision.",
          "2.5× a random 20% list.", "Who gets called this month."]),
        (4.65, MAROON, "FLAG  ·  0.59", "491 people",
         ["Everyone at or above 0.59.", "276 leavers · 215 false alarms.", "Average bill $74.89.",
          "$441,250 of 12-month billing.", "Exposure. Never p × bill."]),
        (8.85, GOLD, "CAMPAIGN ON THE 282", "3.6× scenario",
         ["Cost $14,100 (282 × $50).", "Saved $51,143 · net $37,043.", "35% save, $64.09 bill, 12 mo.",
          "Break-even save rate ≈ 10%.", "Replace 35% with a pilot."]),
    ]
    for x, accent, label, value, lines in cols:
        rect(x, 1.22, 4.00, 5.35, CARD, radius=0.07)
        rect(x, 1.22, 4.00, 0.10, accent)
        text(x + 0.22, 1.65, label, size=11, bold=True, color=MAROON)
        text(x + 0.22, 2.20, value, size=20, bold=True, color=INK)
        for i, line in enumerate(lines):
            text(x + 0.22, 2.75 + i * 0.55, line, size=11, color=INK, max_w=3.55)
    footer(9, "Applications")
    c.showPage()

    # 10
    light_head("Dashboarding",
               "Section 6: the same champion_pipeline, on live controls. No refit. No mock-up.")
    cards([
        {"label": "Who is scored", "value": "One account", "hint": "Same worst-row profile as the waterfall"},
        {"label": "High / Low line", "value": "0.59", "hint": "The flag, not a promise they leave"},
        {"label": "What sliders rebuild", "value": "3 fields", "hint": "TenureBucket, TotalCharges, ChargeRatio"},
        {"label": "What stays fixed", "value": "The rest", "hint": "Payment method and other add-ons"},
    ], y=1.22)
    bullets([
        "Sliders overwrite contract, internet, tenure, bill, Tech Support, and Online Security, then rebuild engineered fields.",
        "Replaying the what-if should land near 81.5% then 69.3% — still High.",
        "Manager: test an offer on one account. Lead: staff the 282. Different screens, one model.",
        "Promote champion_pipeline into app/. Do not retune from the notebook.",
    ], y=2.85)
    takeaway("Takeaway: Dashboard = local what-if. List = who to call. Flag = who is High.")
    footer(10, "Dashboard")
    c.showPage()

    # 11
    light_head("Conclusion",
               "The useful output is a ranked, explainable, costed list — not a leaderboard score.")
    cards([
        {"label": "Holdout capture", "value": "50.8%", "hint": "190 of 374 leavers in 282 contacts"},
        {"label": "Vs a random 20%", "value": "2.5×", "hint": "Same headcount, no model"},
        {"label": "Champion PR-AUC", "value": "0.658", "hint": "Beats logistic 0.635 and no-skill 0.265"},
        {"label": "What is not measured", "value": "35% save", "hint": "The 3.6× multiple waits on a pilot"},
    ], y=1.22)
    bullets([
        "The model recovers the EDA: contract, ChargeRatio, fiber. Demographics are not the targeting rule.",
        "282 is who to call. 491 / $441,250 is exposure. Never mix them. Never p × bill.",
        "SHAP and the what-if move this model, including the over-call. Not a causal claim.",
        "One 80/20 split, random_state=42, one snapshot: who is at risk now.",
    ], y=2.85)
    takeaway("Takeaway: Rank, explain, price. Then measure the save rate before anyone budgets 3.6×.")
    footer(11, "Close")
    c.showPage()

    # 12
    light_head("Recommendations", "Do these in order. Do not start with a dashboard redesign.")
    steps = [
        ("1", "Pilot the 282",
         "Measure the save rate. Until then, 3.6× is a scenario. Break-even is about 10%."),
        ("2", "Staff the list, watch the flag",
         "Capacity follows 282. 0.59 marks High and sizes $441,250. Go deeper only if the pilot saves people."),
        ("3", "Offer contract first, then support",
         "Month-to-month matches SHAP and EDA. Do not promise the worst row clears 0.59."),
        ("4", "Promote the pipeline",
         "Move champion_pipeline into app/. Recalibrate only if you start pricing p × bill × 12."),
    ]
    for i, (num, title, body) in enumerate(steps):
        y = 1.20 + i * 1.35
        rect(0.45, y, 12.43, 1.22, CARD, radius=0.07)
        rect(0.45, y, 1.05, 1.22, MAROON_DARK)
        text(0.97, y + 0.75, num, size=22, bold=True, color=GOLD, align="center")
        text(1.75, y + 0.40, title, size=14, bold=True, color=INK)
        text(1.75, y + 0.80, body, size=12, color=MUTED, max_w=10.8)
    footer(12, "Close")
    c.showPage()

    # 13
    rect(0, 0, SLIDE_W, SLIDE_H, MAROON_DARK)
    rect(0, 0, 0.22, SLIDE_H, GOLD)
    text(0.75, 1.10, "SOURCES AND CONTACT", size=12, bold=True, color=GOLD)
    text(0.75, 1.70, "Staff the list. Watch the flag. Measure the save rate.",
         size=18, bold=True, color=WHITE, max_w=12)
    for i, line in enumerate([
        "IBM. Telco Customer Churn. Public sample, 7,043 customers / 21 features.",
        "Chapman et al. (2000). CRISP-DM 1.0.",
        "Chen & Guestrin (2016). XGBoost. KDD.   ·   Akiba et al. (2019). Optuna. KDD.",
        "Lundberg & Lee (2017). Interpreting model predictions. NeurIPS. (SHAP)",
        "Niculescu-Mizil & Caruana (2005). Predicting good probabilities. ICML.",
        "Code: src/data_pipeline.py, modeling.py, interpretability.py, business_impact.py.",
        "Holdout: 1,409 customers  ·  random_state=42  ·  champion = Optuna-tuned XGBoost.",
    ]):
        text(0.75, 2.40 + i * 0.38, line, size=11, color=CREAM, max_w=11.8)
    text(0.75, 5.90, "Sileshi Hirpa  ·  Business Analytics + Machine Learning",
         size=13, bold=True, color=WHITE)
    text(0.75, 6.30, "W. P. Carey School of Business  ·  Arizona State University",
         size=12, color=GOLD)
    text(0.75, 6.70, "hirpast@gmail.com  ·  linkedin.com/in/sileshi-hirpa  ·  hirpadata.com",
         size=11, color=SOFT)
    c.showPage()
    c.save()


def main():
    prs = build_pptx()
    prs.save(str(PPTX_PATH))
    draw_pdf()
    print(f"Wrote {PPTX_PATH}")
    print(f"Wrote {PDF_PATH}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
