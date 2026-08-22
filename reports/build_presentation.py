"""
Build the executive presentation (PPTX + PDF) from locked notebook numbers.

Source of truth: notebooks/01_churn_analysis.ipynb and the exported
PDF in reports/. All figures on the holdout are 1,409 customers /
374 leavers / 26.5% base unless a slide says training set.
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
PPTX_PATH = OUT_DIR / "Beyond_Accuracy_Churn_Presentation.pptx"
PDF_PATH = OUT_DIR / "Beyond_Accuracy_Churn_Presentation.pdf"

# Widescreen 16:9
SLIDE_W = 13.333
SLIDE_H = 7.5

NAVY_DARK = "#0F2027"
NAVY = "#203A43"
NAVY_MID = "#2C5364"
ORANGE = "#E07A5F"
GREEN = "#3D8361"
PURPLE = "#9C27B0"
TEAL = "#7FD8BE"
BG = "#F4F6F7"
WHITE = "#FFFFFF"
MUTED = "#5B6B73"
LINE = "#D5DCE0"
CARD = "#F4F6F7"


def rgb(hex_color: str) -> RGBColor:
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rl(hex_color: str) -> Color:
    return HexColor(hex_color)


def set_run(paragraph, text, size=18, bold=False, color=NAVY, name="Calibri"):
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


def add_box(slide, x, y, w, h, text, size=16, bold=False, color=NAVY,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, name="Calibri"):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    try:
        tf._txBody.bodyPr.set("anchor", {
            MSO_ANCHOR.TOP: "t",
            MSO_ANCHOR.MIDDLE: "ctr",
            MSO_ANCHOR.BOTTOM: "b",
        }.get(anchor, "t"))
    except Exception:
        pass
    p = tf.paragraphs[0]
    p.alignment = align
    set_run(p, text, size=size, bold=bold, color=color, name=name)
    return box


def add_paras(slide, x, y, w, h, lines, size=16, color=NAVY, spacing=8, bold=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(spacing)
        set_run(p, line, size=size, bold=bold, color=color)
    return box


def add_footer(slide, page, total, section=""):
    add_rect(slide, 0, 7.28, SLIDE_W, 0.03, ORANGE)
    add_box(slide, 0.45, 7.30, 8.5, 0.18,
            f"Beyond Accuracy  ·  Customer Churn{('  ·  ' + section) if section else ''}",
            size=10, color=MUTED)
    add_box(slide, 11.4, 7.30, 1.5, 0.18, f"{page}  /  {total}",
            size=10, color=MUTED, align=PP_ALIGN.RIGHT)


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def add_cards(slide, cards, y=1.55, h=1.35):
    n = len(cards)
    gap = 0.22
    left = 0.45
    width = (SLIDE_W - 0.9 - gap * (n - 1)) / n
    accents = [ORANGE, NAVY_MID, GREEN, PURPLE]
    for i, card in enumerate(cards):
        x = left + i * (width + gap)
        add_rect(slide, x, y, width, h, CARD, rounded=True)
        add_rect(slide, x, y, 0.08, h, accents[i % len(accents)])
        add_box(slide, x + 0.22, y + 0.12, width - 0.34, 0.22,
                card["label"].upper(), size=10, color=MUTED, bold=True)
        add_box(slide, x + 0.22, y + 0.38, width - 0.34, 0.46,
                card["value"], size=22, color=NAVY, bold=True)
        add_box(slide, x + 0.22, y + 0.90, width - 0.34, 0.34,
                card["hint"], size=11, color=MUTED)


def add_takeaway(slide, text, y=6.55):
    add_rect(slide, 0.45, y, 12.43, 0.58, NAVY_DARK, rounded=True)
    add_box(slide, 0.65, y + 0.12, 12.05, 0.36, text,
            size=14, color=WHITE, bold=False, anchor=MSO_ANCHOR.MIDDLE)


def blank_light(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, WHITE)
    return slide


# ---------------------------------------------------------------------------
# Slide content
# ---------------------------------------------------------------------------

TOTAL = 26


def build_pptx() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)
    page = 0

    def next_page():
        nonlocal page
        page += 1
        return page

    # 1 Title ----------------------------------------------------------------
    s = blank_light(prs)
    add_rect(s, 0, 0, SLIDE_W, SLIDE_H, NAVY_DARK)
    add_rect(s, 0, 0, 0.18, SLIDE_H, ORANGE)
    add_box(s, 0.7, 1.35, 12.0, 0.35,
            "CUSTOMER CHURN  ·  APPLIED MACHINE LEARNING",
            size=13, color=TEAL, bold=True)
    add_box(s, 0.7, 1.85, 12.0, 1.7,
            "Beyond Accuracy",
            size=44, color=WHITE, bold=True)
    add_box(s, 0.7, 3.15, 11.5, 1.1,
            "A business-driven, interpretable approach to customer churn prediction",
            size=22, color="#D7E2E9")
    add_box(s, 0.7, 4.55, 11.5, 0.7,
            "Rank the base. Explain the flag. Price the intervention.",
            size=16, color=TEAL)
    add_rect(s, 0.7, 5.45, 2.2, 0.06, ORANGE)
    add_box(s, 0.7, 5.70, 11.5, 0.35,
            "Sileshi Hirpa  ·  Data Scientist, Business Analytics + Machine Learning",
            size=14, color=WHITE)
    add_box(s, 0.7, 6.10, 11.5, 0.35,
            "IBM Telco Customer Churn  ·  7,043 customers  ·  Held-out test of 1,409",
            size=13, color="#D7E2E9")
    add_box(s, 0.7, 6.55, 11.5, 0.3,
            "hirpast@gmail.com  ·  linkedin.com/in/sileshi-hirpa  ·  hirpadata.com",
            size=12, color=MUTED)
    add_notes(s,
        "Open on the title, not the model. The project is a retention decision "
        "system: rank, explain, price. Champion is tuned XGBoost with SHAP. "
        "All later numbers are one 80/20 split on IBM Telco, random_state=42.")
    next_page()

    # 2 Agenda ---------------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.32, 12, 0.45, "Agenda", size=28, color=NAVY, bold=True)
    add_box(s, 0.45, 0.82, 12, 0.35,
            "Six movements. One holdout. No leaderboard-as-the-finish-line.",
            size=15, color=MUTED)
    items = [
        ("01", "The decision", "A ranked call list, a High/Low flag, and a costed scenario."),
        ("02", "Why accuracy fails", "73.5% accurate and zero leavers caught."),
        ("03", "What the data already shows", "Tenure, contract, and price-to-history."),
        ("04", "The champion model", "Tuned XGBoost, a 0.59 flag, and a calibration caveat."),
        ("05", "Why each customer is High", "SHAP that adds back to the model’s own margin."),
        ("06", "What to staff and what to price", "282 contacts. 491 flagged. 3.6× is a scenario."),
    ]
    for i, (num, title, blurb) in enumerate(items):
        col = i % 2
        row = i // 2
        x = 0.45 + col * 6.4
        y = 1.45 + row * 1.7
        add_rect(s, x, y, 6.15, 1.5, CARD, rounded=True)
        add_box(s, x + 0.25, y + 0.22, 1.0, 0.4, num, size=20, color=ORANGE, bold=True)
        add_box(s, x + 1.2, y + 0.25, 4.7, 0.4, title, size=18, color=NAVY, bold=True)
        add_box(s, x + 1.2, y + 0.72, 4.7, 0.55, blurb, size=13, color=MUTED)
    add_footer(s, p, TOTAL, "Overview")
    add_notes(s, "Stay on this slide 15 seconds. Promise you will keep the flag (491) "
              "and the call list (282) separate for the rest of the talk.")

    # 3 Executive snapshot ---------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.45,
            "The useful output is a call list, not a leaderboard",
            size=24, color=NAVY, bold=True)
    add_box(s, 0.45, 0.80, 12.4, 0.35,
            "Same 1,409 held-out customers. Three decisions. Do not mix them.",
            size=15, color=MUTED)
    add_cards(s, [
        {"label": "Ranked list  ·  top 20%", "value": "282 contacts",
         "hint": "190 of 374 leavers  ·  50.8% capture  ·  2.5× random"},
        {"label": "High / Low flag  ·  0.59", "value": "491 accounts",
         "hint": "$441,250 of 12-month billing behind the flag"},
        {"label": "Costed campaign on the 282", "value": "3.6× scenario",
         "hint": "$14,100 cost  ·  $37,043 net  ·  35% save rate"},
    ], y=1.35, h=1.55)
    add_paras(s, 0.55, 3.15, 12.2, 3.1, [
        "Capture (50.8%) is measured on the holdout. The 3.6× multiple is not.",
        "The flag sizes exposure. It is not who gets called this month.",
        "Staff to the ranking. Use 0.59 to say who is High.",
        "A wasted contact is $50 under the campaign assumptions. A missed leaver is a year of bill. F1 treats those as equal — so 0.59 is a conservative proxy, not a budget.",
    ], size=16, spacing=10)
    add_takeaway(s, "Takeaway: 282 to call. 491 to watch. 3.6× only after a pilot replaces the 35% save rate.")
    add_footer(s, p, TOTAL, "The decision")
    add_notes(s,
        "This is the slide a VP should remember. 190/374 into 282 names is 50.8% "
        "at 67.4% precision. Exposure at 0.59 is $441,250 — not a loss forecast. "
        "ROI uses $50/contact, 35% save, $64.09 full-test-set average bill, 12 months.")

    # 4 Accuracy -------------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.5,
            "A model that says “stay” for everyone is already 73.5% accurate",
            size=22, color=NAVY, bold=True)
    add_cards(s, [
        {"label": "Training base rate", "value": "26.5%",
         "hint": "1,495 leavers / 5,634  ·  test stays 26.5%"},
        {"label": "Always-“No” accuracy", "value": "73.5%",
         "hint": "Catches zero of the 1,495 leavers"},
        {"label": "What we optimize", "value": "PR-AUC",
         "hint": "Then recall, then top-20% capture"},
        {"label": "Imbalance treatment", "value": "Weights",
         "hint": "scale_pos_weight ≈ 2.77  ·  no SMOTE"},
    ], y=1.15)
    add_paras(s, 0.55, 2.75, 12.2, 3.4, [
        "The imbalance is real (about 2.8:1) but not extreme. It is not a case for synthetic oversampling.",
        "It is enough that an unweighted loss would drift toward the majority class.",
        "Industry replacement cost is typically 4–5× retention. The question is never only “will they leave?”",
        "It is “which accounts are worth an intervention, what will that cost, and what does it save?”",
    ], size=16, spacing=10)
    add_takeaway(s, "Takeaway: Accuracy is the wrong score. Ranking quality and capture rate are the right ones.")
    add_footer(s, p, TOTAL, "Why accuracy fails")
    add_notes(s, "Training 4,139 stay / 1,495 leave. Stratified 80/20 keeps test at 26.5%. "
              "Weighting keeps the real distribution, which matters for the later calibration discussion.")

    # 5 Objective ------------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.45, "Three success criteria, stated in advance",
            size=24, color=NAVY, bold=True)
    rows = [
        ("01", "A better ranking than chance",
         "PR-AUC on a holdout the model never saw during training or tuning. Champion: 0.658 vs no-skill 0.265."),
        ("02", "A deliberate threshold",
         "Not default 0.50. Peak-F1 at 0.59 becomes the High/Low flag that sizes exposure."),
        ("03", "Explanations that add up",
         "SHAP contributions plus the base rate reconstruct the model’s own raw margin to 2.86e-06."),
        ("04", "A costed case on the same rows",
         "Revenue-at-risk and campaign ROI use the same 1,409 test customers. Assumptions are replaceable."),
    ]
    for i, (num, title, body) in enumerate(rows):
        y = 1.00 + i * 1.25
        add_rect(s, 0.45, y, 12.43, 1.12, CARD, rounded=True)
        add_rect(s, 0.45, y, 0.10, 1.12, [ORANGE, NAVY_MID, GREEN, PURPLE][i])
        add_box(s, 0.75, y + 0.14, 1.0, 0.35, num, size=16, color=ORANGE, bold=True)
        add_box(s, 1.70, y + 0.14, 10.8, 0.35, title, size=18, color=NAVY, bold=True)
        add_box(s, 1.70, y + 0.52, 10.8, 0.45, body, size=14, color=MUTED)
    add_footer(s, p, TOTAL, "Objective")
    add_notes(s, "CRISP-DM framing: business understanding → prepare → model → evaluate → deploy framing. "
              "Leakage screen, shared ColumnTransformer, class weights.")

    # 6 Data -----------------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.45, "One public dataset. One held-out cut.",
            size=26, color=NAVY, bold=True)
    add_cards(s, [
        {"label": "Customers", "value": "7,043",
         "hint": "IBM Telco  ·  21 raw fields"},
        {"label": "Training", "value": "5,634",
         "hint": "80%  ·  stratified on churn"},
        {"label": "Holdout", "value": "1,409",
         "hint": "374 leavers  ·  26.5% base"},
        {"label": "Engineered", "value": "3 signals",
         "hint": "ChargeRatio  ·  TenureBucket  ·  services"},
    ], y=1.05)
    add_paras(s, 0.55, 2.65, 12.2, 3.5, [
        "Fields cover demographics, tenure, services, contract, billing, and the churn label.",
        "customerID is dropped before modeling. ChargeRatio is MonthlyCharges / (TotalCharges + 1).",
        "Leakage screen: ChargeRatio looks identifier-like (96.4% unique) — a false positive. Pearson r ≈ 0.026.",
        "Preprocessor is shared: StandardScaler on numerics, one-hot on categoricals, fit only on train.",
    ], size=16, spacing=10)
    add_takeaway(s, "Takeaway: Later capture and ROI are not an artifact of a shifted test mix. Both splits sit at 26.5%.")
    add_footer(s, p, TOTAL, "Data")
    add_notes(s, "ChargeRatio is almost uncorrelated with MonthlyCharges (r = −0.04) and weakly with tenure (−0.14). "
              "That is why it can outrank the raw bill in SHAP.")

    # 7 Section EDA ----------------------------------------------------------
    s = blank_light(prs)
    add_rect(s, 0, 0, SLIDE_W, SLIDE_H, NAVY_DARK)
    add_rect(s, 0, 0, 0.18, SLIDE_H, ORANGE)
    add_box(s, 0.7, 2.4, 12, 0.4, "01  /  EXPLORATORY ANALYSIS", size=14, color=TEAL, bold=True)
    add_box(s, 0.7, 2.95, 12, 1.2, "The data already ranks risk",
            size=36, color=WHITE, bold=True)
    add_box(s, 0.7, 4.3, 11.5, 0.8,
            "Tenure says when. Contract says how easy. Charges say what they pay — and ChargeRatio says versus history.",
            size=16, color="#D7E2E9")
    next_page()
    add_notes(s, "Do not linger. Promise three charts, then the model.")

    # 8 Tenure ---------------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.5,
            "Leavers leave in the first year",
            size=26, color=NAVY, bold=True)
    add_cards(s, [
        {"label": "Median tenure  ·  leavers", "value": "10 months",
         "hint": "Still inside the dangerous year"},
        {"label": "Median tenure  ·  stayers", "value": "38 months",
         "hint": "Already past it"},
        {"label": "Leavers at or before month 12", "value": "55%",
         "hint": "822 of 1,495 training leavers"},
    ], y=1.15)
    add_paras(s, 0.55, 2.80, 12.2, 3.3, [
        "This is a snapshot, not a survival curve. High-tenure bars are people who already chose to stay.",
        "The chart does not prove that “waiting 38 months” would have saved the 10-month leavers.",
        "It does show where the orange mass sits: the first year, when switching costs are still thin.",
        "TenureBucket (0–1 year vs later) is the explicit cut. Raw tenure stays in so the tree can still split 1 vs 11 months.",
    ], size=16, spacing=10)
    add_takeaway(s, "Takeaway: The risk pool is new. The next chart asks whether “early” is really tenure, or month-to-month.")
    add_footer(s, p, TOTAL, "EDA")
    add_notes(s, "Training-set rates. 55% = 822/1,495. Earlier draft said 53% — do not use that.")

    # 9 Contract -------------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.5,
            "Month-to-month is 55% of the base and 89% of leavers",
            size=22, color=NAVY, bold=True)
    # simple bars
    bars = [
        ("Month-to-month", 0.427, "42.7%", "3,102 accounts  ·  1,326 leavers"),
        ("One year", 0.111, "11.1%", "1,173 accounts  ·  130 leavers"),
        ("Two year", 0.029, "2.9%", "1,359 accounts  ·  39 leavers"),
    ]
    max_v = 0.45
    y0 = 1.20
    for i, (label, val, pct, hint) in enumerate(bars):
        y = y0 + i * 1.15
        add_box(s, 0.55, y, 2.6, 0.35, label, size=16, color=NAVY, bold=True)
        add_box(s, 0.55, y + 0.32, 2.6, 0.35, hint, size=11, color=MUTED)
        add_rect(s, 3.4, y + 0.18, 7.4, 0.38, LINE, rounded=True)
        add_rect(s, 3.4, y + 0.18, 7.4 * (val / max_v), 0.38,
                 ORANGE if i == 0 else NAVY_MID, rounded=True)
        add_box(s, 11.0, y + 0.16, 1.8, 0.42, pct, size=20, color=NAVY, bold=True)
    add_takeaway(s, "Takeaway: A list that ignored contract would still spend most of its time in the orange bar. Association, not a conversion proof.")
    add_footer(s, p, TOTAL, "EDA")
    add_notes(s, "42.7% is 1.6× the 26.5% base and ~15× the two-year rate. "
              "SHAP later puts contract dummies at ~29% of top-15 mass.")

    # 10 Charges -------------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.5,
            "Leavers pay more. The useful feature is bill versus history.",
            size=22, color=NAVY, bold=True)
    add_cards(s, [
        {"label": "Median bill  ·  leavers", "value": "$80",
         "hint": "Mean $75  ·  n = 1,495"},
        {"label": "Median bill  ·  stayers", "value": "$64",
         "hint": "Mean $61  ·  n = 4,139"},
        {"label": "Gap", "value": "+$16 / mo",
         "hint": "Boxes still overlap almost completely"},
        {"label": "ChargeRatio × MonthlyCharges", "value": "r = −0.04",
         "hint": "A different axis from the raw bill"},
    ], y=1.10)
    add_paras(s, 0.55, 2.75, 12.2, 3.4, [
        "A flat “high bill” rule would also flag many stayers. The sharper tell is the floor: leavers rarely sit in the cheap tier.",
        "70% of leavers are on fiber (median fiber bill ~$92) vs 35% of stayers. No-internet sits near $20 and almost never churns.",
        "tenure × TotalCharges = 0.83 is mechanical (rate × time). Trees can use both; SHAP may split the credit.",
        "ChargeRatio later outranks raw MonthlyCharges (12% vs 7% of top-15 SHAP mass). Do not read “charge them less” off the box plot.",
    ], size=15, spacing=9)
    add_takeaway(s, "Takeaway: Price-to-history is the lever. The raw dollar gap is mixed up with fiber and month-to-month.")
    add_footer(s, p, TOTAL, "EDA")
    add_notes(s, "ChargeRatio = MonthlyCharges / (TotalCharges + 1). Weakly related to tenure (r = −0.14).")

    # 11 Section modeling ----------------------------------------------------
    s = blank_light(prs)
    add_rect(s, 0, 0, SLIDE_W, SLIDE_H, NAVY_DARK)
    add_rect(s, 0, 0, 0.18, SLIDE_H, ORANGE)
    add_box(s, 0.7, 2.4, 12, 0.4, "02  /  MODELING", size=14, color=TEAL, bold=True)
    add_box(s, 0.7, 2.95, 12, 1.2, "Rank first. Flag second.",
            size=36, color=WHITE, bold=True)
    add_box(s, 0.7, 4.3, 11.5, 0.8,
            "Same preprocessor. Same weights. One holdout. Tuning has to beat logistic regression or we ship the simpler model.",
            size=16, color="#D7E2E9")
    next_page()
    add_notes(s, "Set up the bake-off. Logistic was first before tuning.")

    # 12 Bake-off ------------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.5,
            "Tuning reversed the bake-off. Champion is regularized XGBoost.",
            size=22, color=NAVY, bold=True)
    models = [
        ("Logistic regression", "0.635", "+0.370 vs no-skill", NAVY_MID),
        ("Random forest", "0.621", "Highest precision @ 0.5", MUTED),
        ("XGBoost, untuned", "0.602", "Why you do not ship defaults", MUTED),
        ("XGBoost, tuned", "0.658", "+0.056 vs untuned  ·  +0.022 vs logistic", ORANGE),
    ]
    for i, (name, val, hint, color) in enumerate(models):
        y = 1.10 + i * 1.05
        add_rect(s, 0.45, y, 12.43, 0.92, CARD, rounded=True)
        add_rect(s, 0.45, y, 0.10, 0.92, color)
        add_box(s, 0.80, y + 0.18, 6.5, 0.35, name, size=18, color=NAVY, bold=True)
        add_box(s, 0.80, y + 0.52, 6.5, 0.28, hint, size=13, color=MUTED)
        add_box(s, 8.6, y + 0.12, 2.2, 0.35, "Test PR-AUC", size=11, color=MUTED)
        add_box(s, 8.6, y + 0.38, 3.8, 0.42, val, size=26, color=NAVY, bold=True)
    add_takeaway(s, "Takeaway: Test 0.658 sits under the CV peak 0.674. That gap is the price of a real holdout, not a failed search.")
    add_footer(s, p, TOTAL, "Modeling")
    add_notes(s,
        "Optuna: 30 trials, 4-fold on 5,634, peaked at trial 6. max_depth=4, 450 trees, "
        "min_child_weight=10, gamma/L1/L2 = 3.9/5.7/3.8. ROC-AUC 0.850. "
        "Recall/precision at 0.5 are ~80%/51% — not the campaign rule.")

    # 13 Threshold -----------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.5,
            "0.59 is the High/Low flag. It is not the call list.",
            size=24, color=NAVY, bold=True)
    add_cards(s, [
        {"label": "Chosen cutoff", "value": "0.59",
         "hint": "F1-max  ·  default is 0.50"},
        {"label": "Precision  /  Recall", "value": "56.2%  /  73.8%",
         "hint": "+5.1 pp  /  −5.9 pp vs 0.50"},
        {"label": "Flagged", "value": "491",
         "hint": "34.8% of 1,409  ·  F1 0.638"},
        {"label": "Confusion", "value": "276 / 215",
         "hint": "TP / FP  ·  FN 98  ·  TN 820"},
    ], y=1.05)
    add_paras(s, 0.55, 2.70, 12.2, 3.4, [
        "Raising the bar from 0.50 to 0.59 is a small F1 move (0.623 → 0.638) and a real headcount move.",
        "276 of 374 leavers sit behind the flag. 215 false alarms still get marked High.",
        "F1 treats a false alarm and a missed leaver as equal. Under the campaign assumptions they are not ($50 vs a year of bill).",
        "A cost-weighted cutoff would sit lower and flag more people. 0.59 is therefore a conservative proxy, not a budget.",
    ], size=15, spacing=9)
    add_takeaway(s, "Takeaway: Staff 282 from the ranking. Use 0.59 to say who is High and to size the $441,250 exposure.")
    add_footer(s, p, TOTAL, "Threshold")
    add_notes(s, "PR-AUC stays 0.658. The sweep only carves a yes/no out of the same ranking.")

    # 14 Calibration ---------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.5,
            "Do not say “0.59 means 59 percent”",
            size=26, color=NAVY, bold=True)
    add_cards(s, [
        {"label": "Brier score", "value": "0.162",
         "hint": "No-skill (always 26.5%) is 0.195"},
        {"label": "Mean predicted", "value": "40.8%",
         "hint": "Observed base rate 26.5%"},
        {"label": "Worst-bin gap", "value": "28.6 pp",
         "hint": "Pred 58%  ·  obs 30%  ·  sits on 0.59"},
        {"label": "Mean abs. error", "value": "14.3 pp",
         "hint": "Same size as the overall bias"},
    ], y=1.10)
    add_paras(s, 0.55, 2.75, 12.2, 3.4, [
        "The reliability curve sits below the diagonal. The model over-calls churn. scale_pos_weight ≈ 2.77 shifted the scoreboard up.",
        "People scored around 0.58 leave at 30% — barely above the base rate. That is why the flag is not a probability.",
        "Two uses stay intact: ranking (5.2) only needs order; exposure (5.3) flags at 0.59 and sums actual bills — it never multiplies by p.",
        "Two uses do not: reading 0.59 out loud as a chance, and treating the 5.5 what-if levels (95.1% → 69.3%) as calibrated probabilities. Direction is usable. Levels are high.",
    ], size=15, spacing=8)
    add_takeaway(s, "Takeaway: Do not retune the champion to chase the diagonal until you price accounts as p × bill × 12.")
    add_footer(s, p, TOTAL, "Calibration")
    add_notes(s, "If that pricing use case appears, apply Platt or isotonic first. Top decile observed churn is still 75.9%.")

    # 15 Section SHAP --------------------------------------------------------
    s = blank_light(prs)
    add_rect(s, 0, 0, SLIDE_W, SLIDE_H, NAVY_DARK)
    add_rect(s, 0, 0, 0.18, SLIDE_H, ORANGE)
    add_box(s, 0.7, 2.4, 12, 0.4, "03  /  INTERPRETABILITY", size=14, color=TEAL, bold=True)
    add_box(s, 0.7, 2.95, 12, 1.2, "Why this person is High",
            size=36, color=WHITE, bold=True)
    add_box(s, 0.7, 4.3, 11.5, 0.8,
            "SHAP explains this champion’s scores — including the over-call. It is not a causal treatment effect.",
            size=16, color="#D7E2E9")
    next_page()
    add_notes(s, "Additivity passed at 2.86e-06 on all 1,409 rows. TreeExplainer on the classifier after the preprocessor.")

    # 16 SHAP global ---------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.45,
            "Contract, ChargeRatio, and fiber are half the model",
            size=24, color=NAVY, bold=True)
    add_box(s, 0.45, 0.78, 12.4, 0.3,
            "Mean absolute SHAP across 1,409 test customers. Share of top-15 mass. Unsigned — direction is in the beeswarm.",
            size=13, color=MUTED)
    add_cards(s, [
        {"label": "Month-to-month", "value": "21%",
         "hint": "Mean |SHAP|  0.565  ·  largest bar"},
        {"label": "All contract dummies", "value": "29%",
         "hint": "Month-to-month + two-year (8%)"},
        {"label": "ChargeRatio", "value": "12%",
         "hint": "Outranks raw MonthlyCharges (7%)"},
        {"label": "Fiber optic", "value": "10%",
         "hint": "Next service lever"},
    ], y=1.15)
    shap_rows = [
        ("Contract_Month-to-month", 0.21, ORANGE),
        ("ChargeRatio", 0.12, ORANGE),
        ("InternetService_Fiber optic", 0.10, ORANGE),
        ("Contract_Two year", 0.08, ORANGE),
        ("MonthlyCharges", 0.07, NAVY_MID),
        ("PaymentMethod_Electronic check", 0.07, NAVY_MID),
        ("tenure", 0.05, NAVY_MID),
    ]
    for i, (name, share, color) in enumerate(shap_rows):
        y = 2.75 + i * 0.42
        add_box(s, 0.55, y, 4.3, 0.35, name, size=13, color=NAVY)
        add_rect(s, 5.0, y + 0.08, 6.4, 0.22, LINE, rounded=True)
        add_rect(s, 5.0, y + 0.08, 6.4 * (share / 0.21), 0.22, color, rounded=True)
        add_box(s, 11.5, y, 1.3, 0.35, f"{share:.0%}", size=13, color=NAVY, bold=True)
    add_takeaway(s, "Takeaway: Levers the company can pull. Gender and senior status are not in the top 15. Not a “switch everyone to two-year” claim.")
    add_footer(s, p, TOTAL, "SHAP")
    add_notes(s,
        "Additivity: max |reconstructed − actual| margin = 2.86e-06. Units are raw margin, not probability. "
        "Month-to-month cohort is scored on contract + ChargeRatio + fiber together. "
        "Already-on-term customers are largely protected by the term itself.")

    # 17 Local / what-if -----------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.5,
            "Worst holdout account: contract is necessary, not sufficient",
            size=22, color=NAVY, bold=True)
    add_cards(s, [
        {"label": "Profile", "value": "1-mo fiber",
         "hint": "$95.10  ·  no support  ·  e-check"},
        {"label": "Baseline score", "value": "95.1%",
         "hint": "Highest-risk test row"},
        {"label": "+ One-year contract", "value": "81.5%",
         "hint": "Still High vs 0.59"},
        {"label": "+ Support + Security", "value": "69.3%",
         "hint": "Still High vs 0.59"},
    ], y=1.10)
    add_paras(s, 0.55, 2.75, 12.2, 3.4, [
        "Local waterfall: ChargeRatio (+0.66) outruns the month-to-month dummy (+0.46) for this row. Fiber, short tenure, and electronic check stack after that.",
        "The talking point is not “the model scored you 0.95.” It is “your bill is high relative to tenure, you are month-to-month, on fiber, paying by e-check.”",
        "Each what-if bar is a rescore of one real test row after fields are overwritten. The model is not refit. MonthlyCharges is not raised — an upper bound, not a priced offer.",
        "Levels sit on the inflated 4.4 scale. Direction is usable. Do not quote 81.5% as a calibrated chance of leaving.",
    ], size=15, spacing=8)
    add_takeaway(s, "Takeaway: Offer a term first. Add support if the local bars say so. Do not promise that row will fall below 0.59.")
    add_footer(s, p, TOTAL, "SHAP")
    add_notes(s, "Cohort reminder: “switch them to a longer contract” only makes sense for month-to-month. "
              "One-year and two-year customers who still look risky need a different lever.")

    # 18 Section business ----------------------------------------------------
    s = blank_light(prs)
    add_rect(s, 0, 0, SLIDE_W, SLIDE_H, NAVY_DARK)
    add_rect(s, 0, 0, 0.18, SLIDE_H, ORANGE)
    add_box(s, 0.7, 2.4, 12, 0.4, "04  /  BUSINESS IMPACT", size=14, color=TEAL, bold=True)
    add_box(s, 0.7, 2.95, 12, 1.2, "What to staff. What to price.",
            size=36, color=WHITE, bold=True)
    add_box(s, 0.7, 4.3, 11.5, 0.8,
            "Ranking decides who is called this month. The flag decides who is marked at risk. Dollars follow those two rules — not each other.",
            size=16, color="#D7E2E9")
    next_page()
    add_notes(s, "Keep 5.2 and 5.3 on separate slides in your head even if you skip one.")

    # 19 Deciles + targeting -------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.5,
            "Top 20% of the ranking holds 50.8% of leavers",
            size=24, color=NAVY, bold=True)
    add_cards(s, [
        {"label": "Decile 1 churn", "value": "75.9%",
         "hint": "107 of 141  ·  2.86× the 26.5% base"},
        {"label": "Top two deciles", "value": "50.8%",
         "hint": "190 of 374 leavers"},
        {"label": "Top-20% list", "value": "282 names",
         "hint": "67.4% precision  ·  2.5× a random 20%"},
        {"label": "Random 20% would catch", "value": "~20%",
         "hint": "Same headcount, no model"},
    ], y=1.10)
    add_paras(s, 0.55, 2.75, 12.2, 3.4, [
        "A useful ranking is a downward staircase. Decile 1 is not a mild lift. It is most of the people in that bucket leaving.",
        "The remaining 184 churners sit further down the list. Reaching them means buying more call capacity, not a different model.",
        "This is the list Section 5.4 prices. It is not the 491-person flag.",
        "Precision on the 282 (67.4%) is higher than precision on the 491 (56.2%) because the list is the top of the ranking, not everyone above 0.59.",
    ], size=15, spacing=8)
    add_takeaway(s, "Takeaway: Same 20% budget: 20% vs 50.8% vs 100% capture. The ranked list is the efficient middle.")
    add_footer(s, p, TOTAL, "Business impact")
    add_notes(s, "100% capture is 5× the effort (the full 1,409). Do not sell that as the plan.")

    # 20 Two uses ------------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.5,
            "Two numbers. Two jobs. Keep them apart.",
            size=26, color=NAVY, bold=True)
    add_rect(s, 0.45, 1.15, 6.05, 4.95, CARD, rounded=True)
    add_rect(s, 0.45, 1.15, 6.05, 0.12, ORANGE)
    add_box(s, 0.70, 1.45, 5.6, 0.4, "CALL LIST  ·  ranking", size=16, color=ORANGE, bold=True)
    add_box(s, 0.70, 1.95, 5.6, 0.5, "282 people", size=32, color=NAVY, bold=True)
    add_paras(s, 0.70, 2.60, 5.6, 3.2, [
        "Top 20% of predicted risk.",
        "190 true leavers.",
        "50.8% capture  ·  67.4% precision.",
        "Who gets called this month.",
        "The campaign in 5.4 prices this list.",
    ], size=15, spacing=8)

    add_rect(s, 6.85, 1.15, 6.05, 4.95, CARD, rounded=True)
    add_rect(s, 6.85, 1.15, 6.05, 0.12, NAVY_MID)
    add_box(s, 7.10, 1.45, 5.6, 0.4, "FLAG  ·  threshold 0.59", size=16, color=NAVY_MID, bold=True)
    add_box(s, 7.10, 1.95, 5.6, 0.5, "491 people", size=32, color=NAVY, bold=True)
    add_paras(s, 7.10, 2.60, 5.6, 3.2, [
        "Everyone at or above 0.59.",
        "276 true leavers  ·  215 false alarms.",
        "Average bill $74.89.",
        "$441,250 of 12-month billing.",
        "Exposure, not a loss forecast. Never p × bill.",
    ], size=15, spacing=8)
    add_footer(s, p, TOTAL, "Business impact")
    add_notes(s, "A deployment uses 0.59 to decide who is at risk and the ranking to decide who gets called. "
              "Do not price the $441k pool as if it were the campaign.")

    # 21 ROI -----------------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.5,
            "3.6× is a scenario until the save rate is measured",
            size=24, color=NAVY, bold=True)
    add_cards(s, [
        {"label": "Campaign cost", "value": "$14,100",
         "hint": "282 × $50  ·  paid on every name"},
        {"label": "Revenue saved", "value": "$51,143",
         "hint": "~66 retained leavers  ·  $64.09 × 12"},
        {"label": "Net benefit", "value": "$37,043",
         "hint": "Saved minus cost on this test set"},
        {"label": "Net ROI", "value": "3.6×",
         "hint": "Break-even save rate ≈ 10%"},
    ], y=1.10)
    add_paras(s, 0.55, 2.75, 12.2, 3.4, [
        "Credit only true churners who are saved: 190 × 35% ≈ 66 accounts. False positives still cost $50 and contribute $0.",
        "Bill used is the cheaper full-test-set mean ($64.09), not the flagged $74.89. That keeps the multiple from looking better than it is.",
        "Replace $50 and 35% with a measured contact cost and a pilot save rate. Until then, do not put 3.6× in a budget.",
        "Even at ~10% save, cost and saved revenue break even. 35% sits well above that line — if the assumption holds.",
    ], size=15, spacing=8)
    add_takeaway(s, "Takeaway: The 190 captured leavers are measured. The 35% save rate is not. Pilot the 282 before you scale.")
    add_footer(s, p, TOTAL, "Business impact")
    add_notes(s, "Formula: cost = 282×50. Saved = 190×0.35×64.09×12. Net = saved − cost. ROI = saved / cost.")

    # 22 Caveats -------------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.45, "What this is not",
            size=28, color=NAVY, bold=True)
    caveats = [
        ("Not a causal claim",
         "SHAP and the what-if cell explain and move the model. They do not prove that converting a contract will cut churn by the scored drop."),
        ("Not a probability you can say out loud",
         "Mean predicted 40.8% vs 26.5% observed. 0.59 is a cut, not a 59% chance. What-if levels are on that inflated scale."),
        ("Not a loss forecast",
         "$441,250 assumes the current bill continues for a year and treats every flagged account as a leaver. Neither is true. It is exposure."),
        ("Not a multi-split result",
         "All metrics are one 80/20 cut at random_state=42. The data are one snapshot: who is at risk now, not whether risk is rising."),
    ]
    for i, (title, body) in enumerate(caveats):
        y = 1.00 + i * 1.30
        add_rect(s, 0.45, y, 12.43, 1.15, CARD, rounded=True)
        add_rect(s, 0.45, y, 0.10, 1.15, ORANGE if i % 2 == 0 else NAVY_MID)
        add_box(s, 0.80, y + 0.16, 11.8, 0.32, title, size=17, color=NAVY, bold=True)
        add_box(s, 0.80, y + 0.52, 11.8, 0.48, body, size=14, color=MUTED)
    add_footer(s, p, TOTAL, "Caveats")
    add_notes(s, "Say this out loud. It is what separates the project from a demo.")

    # 23 Next steps ----------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.45, "Do this next, in order",
            size=28, color=NAVY, bold=True)
    steps = [
        ("1", "Pilot the 282",
         "Hold out a slice so the 35% save rate becomes a measured one. Until that number exists, treat 3.6× as a scenario, not a budget."),
        ("2", "Staff to the list, not the flag",
         "0.59 marks exposure (491). Capacity follows the ranking (282), then deeper only if the pilot actually saves people."),
        ("3", "Promote the pipeline, not a notebook",
         "Move champion_pipeline into app/ with the Section 6 controls as the UI. No change to src/. Revisit 0.59 only after you know monthly capacity."),
    ]
    for i, (num, title, body) in enumerate(steps):
        y = 1.10 + i * 1.70
        add_rect(s, 0.45, y, 12.43, 1.52, CARD, rounded=True)
        add_rect(s, 0.45, y, 1.15, 1.52, NAVY_DARK)
        add_box(s, 0.45, y + 0.45, 1.15, 0.55, num, size=32, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        add_box(s, 1.90, y + 0.22, 10.6, 0.40, title, size=20, color=NAVY, bold=True)
        add_box(s, 1.90, y + 0.70, 10.6, 0.62, body, size=15, color=MUTED)
    add_footer(s, p, TOTAL, "Next steps")
    add_notes(s, "If they ask “what about isotonic?” — only if they start pricing p × bill × 12. Not before.")

    # 24 Appendix metric map -------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.4, "Appendix  ·  Which number for which decision",
            size=24, color=NAVY, bold=True)
    rows = [
        ("Decision", "Number", "Do not use"),
        ("Who to call this month", "Top 20% list  ·  282  ·  190 leavers", "The 491-person flag"),
        ("Who is High / Low", "Threshold 0.59  ·  491 accounts", "“0.59 means 59%”"),
        ("How much billing sits at risk", "$441,250 behind the flag", "p × bill × 12"),
        ("What a campaign might return", "3.6× on $14,100  ·  35% save", "A budget number"),
        ("Why this person is flagged", "Local SHAP  ·  contract, ChargeRatio, fiber", "A global bar as a one-size offer"),
        ("Whether scores are chances", "They are not  ·  mean pred 40.8%", "What-if levels as calibrated %"),
        ("Whether the model ranks", "PR-AUC 0.658  ·  decile 1 = 75.9%", "Accuracy 73.5%"),
    ]
    for i, (a, b, c) in enumerate(rows):
        y = 0.90 + i * 0.70
        bg = NAVY_DARK if i == 0 else (CARD if i % 2 else WHITE)
        tc = WHITE if i == 0 else NAVY
        mc = WHITE if i == 0 else MUTED
        add_rect(s, 0.45, y, 12.43, 0.68, bg)
        add_box(s, 0.60, y + 0.16, 3.6, 0.38, a, size=13, color=tc, bold=True)
        add_box(s, 4.30, y + 0.16, 4.5, 0.38, b, size=13, color=tc)
        add_box(s, 8.90, y + 0.16, 3.8, 0.38, c, size=13, color=mc)
    add_footer(s, p, TOTAL, "Appendix")
    add_notes(s, "Leave this up in Q&A. It prevents the 282/491 mix-up.")

    # 25 References ----------------------------------------------------------
    s = blank_light(prs)
    p = next_page()
    add_box(s, 0.45, 0.28, 12.4, 0.45, "Appendix  ·  Sources",
            size=26, color=NAVY, bold=True)
    add_paras(s, 0.55, 1.00, 12.2, 5.8, [
        "Data. IBM Telco Customer Churn — 7,043 customers, 21 raw fields. Local file: data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv.",
        "Chapman et al. (2000). CRISP-DM 1.0.",
        "Chen & Guestrin (2016). XGBoost. KDD.",
        "Akiba et al. (2019). Optuna. KDD.",
        "Lundberg & Lee (2017). A Unified Approach to Interpreting Model Predictions. NeurIPS. (SHAP)",
        "Niculescu-Mizil & Caruana (2005). Predicting Good Probabilities with Supervised Learning. ICML.",
        "Pedregosa et al. (2011). Scikit-learn. JMLR.",
        "Code. customer-churn-prediction/  ·  src/data_pipeline.py, modeling.py, interpretability.py, business_impact.py.",
        "All holdout metrics: 1,409 customers, random_state=42, champion = Optuna-tuned XGBoost.",
    ], size=15, spacing=9)
    add_footer(s, p, TOTAL, "Appendix")
    add_notes(s, "Optional slide. Skip in a 15-minute briefing.")

    # 26 Close ---------------------------------------------------------------
    s = blank_light(prs)
    add_rect(s, 0, 0, SLIDE_W, SLIDE_H, NAVY_DARK)
    add_rect(s, 0, 0, 0.18, SLIDE_H, ORANGE)
    add_box(s, 0.7, 1.8, 12, 0.4, "THANK YOU", size=14, color=TEAL, bold=True)
    add_box(s, 0.7, 2.3, 12, 1.3, "Staff the list. Watch the flag.\nMeasure the save rate.",
            size=32, color=WHITE, bold=True)
    add_box(s, 0.7, 4.0, 12, 0.5,
            "Sileshi Hirpa  ·  Data Scientist",
            size=18, color=WHITE)
    add_box(s, 0.7, 4.55, 12, 1.0,
            "hirpast@gmail.com\nlinkedin.com/in/sileshi-hirpa  ·  github.com/sileshith  ·  hirpadata.com",
            size=15, color="#D7E2E9")
    add_box(s, 0.7, 6.2, 12, 0.4,
            "Notebook + source  ·  customer-churn-prediction/",
            size=13, color=MUTED)
    next_page()
    add_notes(s, "Close on the three actions. Take questions from the metric-map appendix.")

    assert page == TOTAL, f"Expected {TOTAL} slides, built {page}"
    return prs


# ---------------------------------------------------------------------------
# PDF mirror
# ---------------------------------------------------------------------------

def wrap(c, text, font, size, max_width):
    return simpleSplit(text, font, size, max_width)


def draw_pdf():
    c = pdf_canvas.Canvas(str(PDF_PATH), pagesize=(SLIDE_W * 72, SLIDE_H * 72))
    W, H = SLIDE_W * 72, SLIDE_H * 72

    def inch(x, y=None):
        if y is None:
            return x * 72
        return x * 72, H - y * 72

    def rect(x, y, w, h, fill, radius=0):
        c.setFillColor(rl(fill))
        c.setStrokeColor(rl(fill))
        if radius:
            c.roundRect(x * 72, H - (y + h) * 72, w * 72, h * 72, radius * 72, fill=1, stroke=0)
        else:
            c.rect(x * 72, H - (y + h) * 72, w * 72, h * 72, fill=1, stroke=0)

    def text(x, y, msg, size=16, bold=False, color=NAVY, align="left", max_w=None):
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.setFillColor(rl(color))
        px, py = x * 72, H - y * 72 - size
        if max_w:
            lines = wrap(c, msg, font, size, max_w * 72)
            for i, line in enumerate(lines):
                yy = py - i * (size + 4)
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
        rect(0, 7.28, SLIDE_W, 0.03, ORANGE)
        text(0.45, 7.48, f"Beyond Accuracy  ·  Customer Churn{('  ·  ' + section) if section else ''}",
             size=9, color=MUTED)
        text(12.9, 7.48, f"{page}  /  {TOTAL}", size=9, color=MUTED, align="right")

    def cards(items, y=1.55, h=1.35):
        n = len(items)
        gap = 0.22
        left = 0.45
        width = (SLIDE_W - 0.9 - gap * (n - 1)) / n
        accents = [ORANGE, NAVY_MID, GREEN, PURPLE]
        for i, card in enumerate(items):
            x = left + i * (width + gap)
            rect(x, y, width, h, CARD, radius=0.08)
            rect(x, y, 0.08, h, accents[i % 4])
            text(x + 0.22, y + 0.28, card["label"].upper(), size=9, bold=True, color=MUTED)
            text(x + 0.22, y + 0.70, card["value"], size=16, bold=True, color=NAVY, max_w=width - 0.4)
            text(x + 0.22, y + 1.12, card["hint"], size=9, color=MUTED, max_w=width - 0.4)

    def takeaway(msg, y=6.58):
        rect(0.45, y, 12.43, 0.55, NAVY_DARK, radius=0.06)
        text(0.65, y + 0.36, msg, size=11, color=WHITE, max_w=12.0)

    def bullets(lines, x=0.55, y=2.85, size=12, leading=0.38):
        for i, line in enumerate(lines):
            text(x, y + i * leading, line, size=size, color=NAVY, max_w=12.2)

    def section_slide(kicker, title, blurb):
        rect(0, 0, SLIDE_W, SLIDE_H, NAVY_DARK)
        rect(0, 0, 0.18, SLIDE_H, ORANGE)
        text(0.7, 2.7, kicker, size=12, bold=True, color=TEAL)
        text(0.7, 3.5, title, size=32, bold=True, color=WHITE, max_w=12)
        text(0.7, 4.6, blurb, size=13, color="#D7E2E9", max_w=11.5)

    def light():
        rect(0, 0, SLIDE_W, SLIDE_H, WHITE)

    # 1
    rect(0, 0, SLIDE_W, SLIDE_H, NAVY_DARK)
    rect(0, 0, 0.18, SLIDE_H, ORANGE)
    text(0.7, 1.7, "CUSTOMER CHURN  ·  APPLIED MACHINE LEARNING", size=12, bold=True, color=TEAL)
    text(0.7, 2.55, "Beyond Accuracy", size=40, bold=True, color=WHITE)
    text(0.7, 3.5, "A business-driven, interpretable approach to customer churn prediction",
         size=16, color="#D7E2E9", max_w=11.5)
    text(0.7, 4.5, "Rank the base. Explain the flag. Price the intervention.", size=13, color=TEAL)
    rect(0.7, 5.45, 2.2, 0.05, ORANGE)
    text(0.7, 5.95, "Sileshi Hirpa  ·  Data Scientist, Business Analytics + Machine Learning",
         size=12, color=WHITE)
    text(0.7, 6.35, "IBM Telco Customer Churn  ·  7,043 customers  ·  Held-out test of 1,409",
         size=11, color="#D7E2E9")
    text(0.7, 6.80, "hirpast@gmail.com  ·  linkedin.com/in/sileshi-hirpa  ·  hirpadata.com",
         size=10, color=MUTED)
    c.showPage()

    # 2
    light()
    text(0.45, 0.55, "Agenda", size=24, bold=True, color=NAVY)
    text(0.45, 1.00, "Six movements. One holdout. No leaderboard-as-the-finish-line.", size=12, color=MUTED)
    items = [
        ("01", "The decision", "A ranked call list, a High/Low flag, and a costed scenario."),
        ("02", "Why accuracy fails", "73.5% accurate and zero leavers caught."),
        ("03", "What the data already shows", "Tenure, contract, and price-to-history."),
        ("04", "The champion model", "Tuned XGBoost, a 0.59 flag, and a calibration caveat."),
        ("05", "Why each customer is High", "SHAP that adds back to the model’s own margin."),
        ("06", "What to staff and what to price", "282 contacts. 491 flagged. 3.6× is a scenario."),
    ]
    for i, (num, title, blurb) in enumerate(items):
        col, row = i % 2, i // 2
        x, y = 0.45 + col * 6.4, 1.40 + row * 1.7
        rect(x, y, 6.15, 1.5, CARD, radius=0.08)
        text(x + 0.25, y + 0.45, num, size=16, bold=True, color=ORANGE)
        text(x + 1.2, y + 0.45, title, size=14, bold=True, color=NAVY)
        text(x + 1.2, y + 0.95, blurb, size=11, color=MUTED, max_w=4.7)
    footer(2, "Overview")
    c.showPage()

    # 3
    light()
    text(0.45, 0.50, "The useful output is a call list, not a leaderboard", size=20, bold=True, color=NAVY, max_w=12.4)
    text(0.45, 0.95, "Same 1,409 held-out customers. Three decisions. Do not mix them.", size=12, color=MUTED)
    cards([
        {"label": "Ranked list  ·  top 20%", "value": "282 contacts",
         "hint": "190 of 374 leavers  ·  50.8% capture  ·  2.5× random"},
        {"label": "High / Low flag  ·  0.59", "value": "491 accounts",
         "hint": "$441,250 of 12-month billing behind the flag"},
        {"label": "Costed campaign on the 282", "value": "3.6× scenario",
         "hint": "$14,100 cost  ·  $37,043 net  ·  35% save rate"},
    ], y=1.25, h=1.50)
    bullets([
        "Capture (50.8%) is measured on the holdout. The 3.6× multiple is not.",
        "The flag sizes exposure. It is not who gets called this month.",
        "Staff to the ranking. Use 0.59 to say who is High.",
        "A wasted contact is $50. A missed leaver is a year of bill. F1 treats those as equal.",
    ], y=3.15)
    takeaway("Takeaway: 282 to call. 491 to watch. 3.6× only after a pilot replaces the 35% save rate.")
    footer(3, "The decision")
    c.showPage()

    # 4
    light()
    text(0.45, 0.50, "A model that says “stay” for everyone is already 73.5% accurate",
         size=18, bold=True, color=NAVY, max_w=12.4)
    cards([
        {"label": "Training base rate", "value": "26.5%", "hint": "1,495 leavers / 5,634  ·  test stays 26.5%"},
        {"label": "Always-“No” accuracy", "value": "73.5%", "hint": "Catches zero of the 1,495 leavers"},
        {"label": "What we optimize", "value": "PR-AUC", "hint": "Then recall, then top-20% capture"},
        {"label": "Imbalance treatment", "value": "Weights", "hint": "scale_pos_weight ≈ 2.77  ·  no SMOTE"},
    ], y=1.10)
    bullets([
        "The imbalance is real (about 2.8:1) but not extreme. Not a case for SMOTE.",
        "It is enough that an unweighted loss would drift toward the majority class.",
        "Replacement typically costs 4–5× retention. The question is who is worth an intervention.",
        "Then: what will that intervention cost, and what does it save?",
    ], y=2.80)
    takeaway("Takeaway: Accuracy is the wrong score. Ranking quality and capture rate are the right ones.")
    footer(4, "Why accuracy fails")
    c.showPage()

    # 5
    light()
    text(0.45, 0.50, "Three success criteria, stated in advance", size=22, bold=True, color=NAVY)
    rows = [
        ("01", "A better ranking than chance",
         "PR-AUC on a holdout the model never saw. Champion: 0.658 vs no-skill 0.265."),
        ("02", "A deliberate threshold",
         "Not default 0.50. Peak-F1 at 0.59 becomes the High/Low flag that sizes exposure."),
        ("03", "Explanations that add up",
         "SHAP plus the base rate reconstruct the model’s raw margin to 2.86e-06."),
        ("04", "A costed case on the same rows",
         "Revenue-at-risk and ROI use the same 1,409 test customers. Assumptions are replaceable."),
    ]
    for i, (num, title, body) in enumerate(rows):
        y = 1.00 + i * 1.25
        rect(0.45, y, 12.43, 1.12, CARD, radius=0.07)
        rect(0.45, y, 0.10, 1.12, [ORANGE, NAVY_MID, GREEN, PURPLE][i])
        text(0.75, y + 0.40, num, size=14, bold=True, color=ORANGE)
        text(1.70, y + 0.40, title, size=14, bold=True, color=NAVY)
        text(1.70, y + 0.80, body, size=11, color=MUTED, max_w=10.8)
    footer(5, "Objective")
    c.showPage()

    # 6
    light()
    text(0.45, 0.50, "One public dataset. One held-out cut.", size=22, bold=True, color=NAVY)
    cards([
        {"label": "Customers", "value": "7,043", "hint": "IBM Telco  ·  21 raw fields"},
        {"label": "Training", "value": "5,634", "hint": "80%  ·  stratified on churn"},
        {"label": "Holdout", "value": "1,409", "hint": "374 leavers  ·  26.5% base"},
        {"label": "Engineered", "value": "3 signals", "hint": "ChargeRatio  ·  TenureBucket  ·  services"},
    ], y=1.05)
    bullets([
        "Fields cover demographics, tenure, services, contract, billing, and the churn label.",
        "customerID is dropped. ChargeRatio = MonthlyCharges / (TotalCharges + 1).",
        "Leakage screen: ChargeRatio looks identifier-like (96.4% unique) — a false positive. r ≈ 0.026.",
        "Shared preprocessor, fit only on train: StandardScaler + one-hot.",
    ], y=2.70)
    takeaway("Takeaway: Later capture and ROI are not an artifact of a shifted test mix. Both splits sit at 26.5%.")
    footer(6, "Data")
    c.showPage()

    # 7
    section_slide("01  /  EXPLORATORY ANALYSIS", "The data already ranks risk",
                  "Tenure says when. Contract says how easy. Charges say what they pay — and ChargeRatio says versus history.")
    c.showPage()

    # 8
    light()
    text(0.45, 0.50, "Leavers leave in the first year", size=22, bold=True, color=NAVY)
    cards([
        {"label": "Median tenure  ·  leavers", "value": "10 months", "hint": "Still inside the dangerous year"},
        {"label": "Median tenure  ·  stayers", "value": "38 months", "hint": "Already past it"},
        {"label": "Leavers at or before month 12", "value": "55%", "hint": "822 of 1,495 training leavers"},
    ], y=1.15)
    bullets([
        "This is a snapshot, not a survival curve. High-tenure bars already chose to stay.",
        "It does not prove that “waiting 38 months” would have saved the 10-month leavers.",
        "The orange mass sits in the first year, when switching costs are still thin.",
        "TenureBucket is the explicit cut. Raw tenure stays in so the tree can split 1 vs 11 months.",
    ], y=2.85)
    takeaway("Takeaway: The risk pool is new. The next chart asks whether “early” is tenure or month-to-month.")
    footer(8, "EDA")
    c.showPage()

    # 9
    light()
    text(0.45, 0.50, "Month-to-month is 55% of the base and 89% of leavers",
         size=18, bold=True, color=NAVY, max_w=12.4)
    bars = [
        ("Month-to-month", 0.427, "42.7%", "3,102 accounts  ·  1,326 leavers"),
        ("One year", 0.111, "11.1%", "1,173 accounts  ·  130 leavers"),
        ("Two year", 0.029, "2.9%", "1,359 accounts  ·  39 leavers"),
    ]
    for i, (label, val, pct, hint) in enumerate(bars):
        y = 1.20 + i * 1.15
        text(0.55, y + 0.30, label, size=13, bold=True, color=NAVY)
        text(0.55, y + 0.62, hint, size=10, color=MUTED)
        rect(3.4, y + 0.22, 7.4, 0.38, LINE, radius=0.04)
        rect(3.4, y + 0.22, 7.4 * (val / 0.45), 0.38, ORANGE if i == 0 else NAVY_MID, radius=0.04)
        text(11.1, y + 0.48, pct, size=16, bold=True, color=NAVY)
    takeaway("Takeaway: A list that ignored contract would still spend most of its time in the orange bar.")
    footer(9, "EDA")
    c.showPage()

    # 10
    light()
    text(0.45, 0.50, "Leavers pay more. The useful feature is bill versus history.",
         size=18, bold=True, color=NAVY, max_w=12.4)
    cards([
        {"label": "Median bill  ·  leavers", "value": "$80", "hint": "Mean $75  ·  n = 1,495"},
        {"label": "Median bill  ·  stayers", "value": "$64", "hint": "Mean $61  ·  n = 4,139"},
        {"label": "Gap", "value": "+$16 / mo", "hint": "Boxes still overlap almost completely"},
        {"label": "ChargeRatio × MonthlyCharges", "value": "r = −0.04", "hint": "A different axis from the raw bill"},
    ], y=1.10)
    bullets([
        "A flat “high bill” rule would also flag many stayers.",
        "70% of leavers are on fiber vs 35% of stayers. No-internet almost never churns.",
        "tenure × TotalCharges = 0.83 is mechanical. SHAP may split the credit.",
        "ChargeRatio later outranks raw MonthlyCharges (12% vs 7% of top-15 SHAP mass).",
    ], y=2.80)
    takeaway("Takeaway: Price-to-history is the lever. The raw dollar gap is mixed up with fiber and month-to-month.")
    footer(10, "EDA")
    c.showPage()

    # 11
    section_slide("02  /  MODELING", "Rank first. Flag second.",
                  "Same preprocessor. Same weights. One holdout. Tuning has to beat logistic or we ship the simpler model.")
    c.showPage()

    # 12
    light()
    text(0.45, 0.50, "Tuning reversed the bake-off. Champion is regularized XGBoost.",
         size=18, bold=True, color=NAVY, max_w=12.4)
    models = [
        ("Logistic regression", "0.635", "+0.370 vs no-skill", NAVY_MID),
        ("Random forest", "0.621", "Highest precision @ 0.5", MUTED),
        ("XGBoost, untuned", "0.602", "Why you do not ship defaults", MUTED),
        ("XGBoost, tuned", "0.658", "+0.056 vs untuned  ·  +0.022 vs logistic", ORANGE),
    ]
    for i, (name, val, hint, color) in enumerate(models):
        y = 1.10 + i * 1.05
        rect(0.45, y, 12.43, 0.92, CARD, radius=0.07)
        rect(0.45, y, 0.10, 0.92, color)
        text(0.80, y + 0.38, name, size=14, bold=True, color=NAVY)
        text(0.80, y + 0.70, hint, size=11, color=MUTED)
        text(8.6, y + 0.32, "Test PR-AUC", size=9, color=MUTED)
        text(8.6, y + 0.72, val, size=22, bold=True, color=NAVY)
    takeaway("Takeaway: Test 0.658 sits under the CV peak 0.674. That gap is the price of a real holdout.")
    footer(12, "Modeling")
    c.showPage()

    # 13
    light()
    text(0.45, 0.50, "0.59 is the High/Low flag. It is not the call list.",
         size=20, bold=True, color=NAVY)
    cards([
        {"label": "Chosen cutoff", "value": "0.59", "hint": "F1-max  ·  default is 0.50"},
        {"label": "Precision  /  Recall", "value": "56.2%  /  73.8%", "hint": "+5.1 pp  /  −5.9 pp vs 0.50"},
        {"label": "Flagged", "value": "491", "hint": "34.8% of 1,409  ·  F1 0.638"},
        {"label": "Confusion", "value": "276 / 215", "hint": "TP / FP  ·  FN 98  ·  TN 820"},
    ], y=1.05)
    bullets([
        "Raising 0.50 to 0.59 is a small F1 move (0.623 → 0.638) and a real headcount move.",
        "276 of 374 leavers sit behind the flag. 215 false alarms are still marked High.",
        "F1 treats a false alarm and a missed leaver as equal. Under the campaign they are not.",
        "A cost-weighted cutoff would sit lower. 0.59 is a conservative proxy, not a budget.",
    ], y=2.75)
    takeaway("Takeaway: Staff 282 from the ranking. Use 0.59 to say who is High and to size $441,250.")
    footer(13, "Threshold")
    c.showPage()

    # 14
    light()
    text(0.45, 0.50, "Do not say “0.59 means 59 percent”", size=22, bold=True, color=NAVY)
    cards([
        {"label": "Brier score", "value": "0.162", "hint": "No-skill (always 26.5%) is 0.195"},
        {"label": "Mean predicted", "value": "40.8%", "hint": "Observed base rate 26.5%"},
        {"label": "Worst-bin gap", "value": "28.6 pp", "hint": "Pred 58%  ·  obs 30%  ·  sits on 0.59"},
        {"label": "Mean abs. error", "value": "14.3 pp", "hint": "Same size as the overall bias"},
    ], y=1.10)
    bullets([
        "The curve sits below the diagonal. scale_pos_weight ≈ 2.77 shifted the scoreboard up.",
        "People scored around 0.58 leave at 30%. That is why the flag is not a probability.",
        "Ranking and flag-then-sum-bills still hold. They never multiply by p.",
        "What-if levels (95.1% → 69.3%) are on an inflated scale. Direction is usable.",
    ], y=2.80)
    takeaway("Takeaway: Do not retune the champion to chase the diagonal until you price p × bill × 12.")
    footer(14, "Calibration")
    c.showPage()

    # 15
    section_slide("03  /  INTERPRETABILITY", "Why this person is High",
                  "SHAP explains this champion’s scores — including the over-call. It is not a causal treatment effect.")
    c.showPage()

    # 16
    light()
    text(0.45, 0.50, "Contract, ChargeRatio, and fiber are half the model",
         size=18, bold=True, color=NAVY, max_w=12.4)
    text(0.45, 0.90, "Mean absolute SHAP across 1,409 test customers. Share of top-15 mass.",
         size=11, color=MUTED)
    cards([
        {"label": "Month-to-month", "value": "21%", "hint": "Mean |SHAP|  0.565  ·  largest bar"},
        {"label": "All contract dummies", "value": "29%", "hint": "Month-to-month + two-year (8%)"},
        {"label": "ChargeRatio", "value": "12%", "hint": "Outranks raw MonthlyCharges (7%)"},
        {"label": "Fiber optic", "value": "10%", "hint": "Next service lever"},
    ], y=1.10)
    shap_rows = [
        ("Contract_Month-to-month", 0.21, ORANGE),
        ("ChargeRatio", 0.12, ORANGE),
        ("InternetService_Fiber optic", 0.10, ORANGE),
        ("Contract_Two year", 0.08, ORANGE),
        ("MonthlyCharges", 0.07, NAVY_MID),
        ("PaymentMethod_Electronic check", 0.07, NAVY_MID),
        ("tenure", 0.05, NAVY_MID),
    ]
    for i, (name, share, color) in enumerate(shap_rows):
        y = 2.70 + i * 0.42
        text(0.55, y + 0.28, name, size=11, color=NAVY)
        rect(5.0, y + 0.10, 6.4, 0.22, LINE, radius=0.03)
        rect(5.0, y + 0.10, 6.4 * (share / 0.21), 0.22, color, radius=0.03)
        text(11.6, y + 0.28, f"{share:.0%}", size=11, bold=True, color=NAVY)
    takeaway("Takeaway: Levers the company can pull. Gender and senior status are not in the top 15.")
    footer(16, "SHAP")
    c.showPage()

    # 17
    light()
    text(0.45, 0.50, "Worst holdout account: contract is necessary, not sufficient",
         size=18, bold=True, color=NAVY, max_w=12.4)
    cards([
        {"label": "Profile", "value": "1-mo fiber", "hint": "$95.10  ·  no support  ·  e-check"},
        {"label": "Baseline score", "value": "95.1%", "hint": "Highest-risk test row"},
        {"label": "+ One-year contract", "value": "81.5%", "hint": "Still High vs 0.59"},
        {"label": "+ Support + Security", "value": "69.3%", "hint": "Still High vs 0.59"},
    ], y=1.10)
    bullets([
        "Local waterfall: ChargeRatio (+0.66) outruns month-to-month (+0.46) on this row.",
        "Talking point: high bill vs tenure, month-to-month, fiber, electronic check.",
        "Each bar is a rescore of one real test row. MonthlyCharges is not raised.",
        "Levels sit on the inflated 4.4 scale. Do not quote 81.5% as a calibrated chance.",
    ], y=2.80)
    takeaway("Takeaway: Offer a term first. Add support if the local bars say so. That row stays High.")
    footer(17, "SHAP")
    c.showPage()

    # 18
    section_slide("04  /  BUSINESS IMPACT", "What to staff. What to price.",
                  "Ranking decides who is called this month. The flag decides who is marked at risk.")
    c.showPage()

    # 19
    light()
    text(0.45, 0.50, "Top 20% of the ranking holds 50.8% of leavers",
         size=20, bold=True, color=NAVY)
    cards([
        {"label": "Decile 1 churn", "value": "75.9%", "hint": "107 of 141  ·  2.86× the 26.5% base"},
        {"label": "Top two deciles", "value": "50.8%", "hint": "190 of 374 leavers"},
        {"label": "Top-20% list", "value": "282 names", "hint": "67.4% precision  ·  2.5× a random 20%"},
        {"label": "Random 20% would catch", "value": "~20%", "hint": "Same headcount, no model"},
    ], y=1.10)
    bullets([
        "A useful ranking is a downward staircase. Decile 1 is most of that bucket leaving.",
        "The remaining 184 churners sit further down. Reaching them means more capacity.",
        "This is the list Section 5.4 prices. It is not the 491-person flag.",
        "Precision on the 282 (67.4%) beats precision on the 491 (56.2%).",
    ], y=2.80)
    takeaway("Takeaway: Same 20% budget: 20% vs 50.8% vs 100% capture. The ranked list is the efficient middle.")
    footer(19, "Business impact")
    c.showPage()

    # 20
    light()
    text(0.45, 0.50, "Two numbers. Two jobs. Keep them apart.", size=22, bold=True, color=NAVY)
    rect(0.45, 1.15, 6.05, 4.95, CARD, radius=0.08)
    rect(0.45, 1.15, 6.05, 0.12, ORANGE)
    text(0.70, 1.70, "CALL LIST  ·  ranking", size=12, bold=True, color=ORANGE)
    text(0.70, 2.30, "282 people", size=26, bold=True, color=NAVY)
    for i, line in enumerate([
        "Top 20% of predicted risk.",
        "190 true leavers.",
        "50.8% capture  ·  67.4% precision.",
        "Who gets called this month.",
        "The campaign in 5.4 prices this list.",
    ]):
        text(0.70, 2.85 + i * 0.42, line, size=12, color=NAVY)
    rect(6.85, 1.15, 6.05, 4.95, CARD, radius=0.08)
    rect(6.85, 1.15, 6.05, 0.12, NAVY_MID)
    text(7.10, 1.70, "FLAG  ·  threshold 0.59", size=12, bold=True, color=NAVY_MID)
    text(7.10, 2.30, "491 people", size=26, bold=True, color=NAVY)
    for i, line in enumerate([
        "Everyone at or above 0.59.",
        "276 true leavers  ·  215 false alarms.",
        "Average bill $74.89.",
        "$441,250 of 12-month billing.",
        "Exposure, not a loss forecast. Never p × bill.",
    ]):
        text(7.10, 2.85 + i * 0.42, line, size=12, color=NAVY)
    footer(20, "Business impact")
    c.showPage()

    # 21
    light()
    text(0.45, 0.50, "3.6× is a scenario until the save rate is measured",
         size=20, bold=True, color=NAVY)
    cards([
        {"label": "Campaign cost", "value": "$14,100", "hint": "282 × $50  ·  paid on every name"},
        {"label": "Revenue saved", "value": "$51,143", "hint": "~66 retained leavers  ·  $64.09 × 12"},
        {"label": "Net benefit", "value": "$37,043", "hint": "Saved minus cost on this test set"},
        {"label": "Net ROI", "value": "3.6×", "hint": "Break-even save rate ≈ 10%"},
    ], y=1.10)
    bullets([
        "Credit only true churners who are saved: 190 × 35% ≈ 66. False positives still cost $50.",
        "Bill used is the cheaper test-set mean ($64.09), not the flagged $74.89.",
        "Replace $50 and 35% with a measured contact cost and a pilot save rate.",
        "Even at ~10% save, cost and saved revenue break even — if the assumption holds.",
    ], y=2.80)
    takeaway("Takeaway: The 190 captured leavers are measured. The 35% save rate is not. Pilot the 282.")
    footer(21, "Business impact")
    c.showPage()

    # 22
    light()
    text(0.45, 0.50, "What this is not", size=24, bold=True, color=NAVY)
    caveats = [
        ("Not a causal claim",
         "SHAP and the what-if cell explain and move the model. They do not prove a treatment effect."),
        ("Not a probability you can say out loud",
         "Mean predicted 40.8% vs 26.5% observed. 0.59 is a cut, not a 59% chance."),
        ("Not a loss forecast",
         "$441,250 assumes the current bill continues for a year and treats every flagged account as a leaver."),
        ("Not a multi-split result",
         "All metrics are one 80/20 cut at random_state=42. One snapshot: who is at risk now."),
    ]
    for i, (title, body) in enumerate(caveats):
        y = 1.00 + i * 1.30
        rect(0.45, y, 12.43, 1.15, CARD, radius=0.07)
        rect(0.45, y, 0.10, 1.15, ORANGE if i % 2 == 0 else NAVY_MID)
        text(0.80, y + 0.40, title, size=14, bold=True, color=NAVY)
        text(0.80, y + 0.80, body, size=12, color=MUTED, max_w=11.8)
    footer(22, "Caveats")
    c.showPage()

    # 23
    light()
    text(0.45, 0.50, "Do this next, in order", size=24, bold=True, color=NAVY)
    steps = [
        ("1", "Pilot the 282",
         "Hold out a slice so the 35% save rate becomes a measured one. Until then, 3.6× is a scenario."),
        ("2", "Staff to the list, not the flag",
         "0.59 marks exposure (491). Capacity follows the ranking (282), then deeper only if the pilot saves people."),
        ("3", "Promote the pipeline, not a notebook",
         "Move champion_pipeline into app/. Revisit 0.59 only after you know monthly capacity."),
    ]
    for i, (num, title, body) in enumerate(steps):
        y = 1.10 + i * 1.70
        rect(0.45, y, 12.43, 1.52, CARD, radius=0.08)
        rect(0.45, y, 1.15, 1.52, NAVY_DARK)
        text(1.02, y + 0.90, num, size=28, bold=True, color=WHITE, align="center")
        text(1.90, y + 0.45, title, size=16, bold=True, color=NAVY)
        text(1.90, y + 0.95, body, size=12, color=MUTED, max_w=10.6)
    footer(23, "Next steps")
    c.showPage()

    # 24
    light()
    text(0.45, 0.50, "Appendix  ·  Which number for which decision", size=20, bold=True, color=NAVY)
    rows = [
        ("Decision", "Number", "Do not use"),
        ("Who to call this month", "Top 20% list  ·  282  ·  190 leavers", "The 491-person flag"),
        ("Who is High / Low", "Threshold 0.59  ·  491 accounts", "“0.59 means 59%”"),
        ("How much billing sits at risk", "$441,250 behind the flag", "p × bill × 12"),
        ("What a campaign might return", "3.6× on $14,100  ·  35% save", "A budget number"),
        ("Why this person is flagged", "Local SHAP  ·  contract, ChargeRatio, fiber", "A global bar as a one-size offer"),
        ("Whether scores are chances", "They are not  ·  mean pred 40.8%", "What-if levels as calibrated %"),
        ("Whether the model ranks", "PR-AUC 0.658  ·  decile 1 = 75.9%", "Accuracy 73.5%"),
    ]
    for i, (a, b, d) in enumerate(rows):
        y = 0.90 + i * 0.70
        bg = NAVY_DARK if i == 0 else (CARD if i % 2 else WHITE)
        tc = WHITE if i == 0 else NAVY
        mc = WHITE if i == 0 else MUTED
        rect(0.45, y, 12.43, 0.68, bg)
        text(0.60, y + 0.42, a, size=11, bold=True, color=tc)
        text(4.30, y + 0.42, b, size=11, color=tc)
        text(8.90, y + 0.42, d, size=11, color=mc)
    footer(24, "Appendix")
    c.showPage()

    # 25
    light()
    text(0.45, 0.50, "Appendix  ·  Sources", size=22, bold=True, color=NAVY)
    bullets([
        "Data. IBM Telco Customer Churn — 7,043 customers, 21 raw fields.",
        "Chapman et al. (2000). CRISP-DM 1.0.",
        "Chen & Guestrin (2016). XGBoost. KDD.",
        "Akiba et al. (2019). Optuna. KDD.",
        "Lundberg & Lee (2017). Interpreting Model Predictions. NeurIPS. (SHAP)",
        "Niculescu-Mizil & Caruana (2005). Predicting Good Probabilities. ICML.",
        "Pedregosa et al. (2011). Scikit-learn. JMLR.",
        "Code. src/data_pipeline.py, modeling.py, interpretability.py, business_impact.py.",
        "Holdout metrics: 1,409 customers, random_state=42, champion = Optuna-tuned XGBoost.",
    ], y=1.10, leading=0.48)
    footer(25, "Appendix")
    c.showPage()

    # 26
    rect(0, 0, SLIDE_W, SLIDE_H, NAVY_DARK)
    rect(0, 0, 0.18, SLIDE_H, ORANGE)
    text(0.7, 2.10, "THANK YOU", size=12, bold=True, color=TEAL)
    text(0.7, 2.80, "Staff the list. Watch the flag.", size=28, bold=True, color=WHITE)
    text(0.7, 3.40, "Measure the save rate.", size=28, bold=True, color=WHITE)
    text(0.7, 4.30, "Sileshi Hirpa  ·  Data Scientist", size=14, color=WHITE)
    text(0.7, 4.80, "hirpast@gmail.com", size=12, color="#D7E2E9")
    text(0.7, 5.20, "linkedin.com/in/sileshi-hirpa  ·  github.com/sileshith  ·  hirpadata.com",
         size=12, color="#D7E2E9")
    text(0.7, 6.30, "Notebook + source  ·  customer-churn-prediction/", size=11, color=MUTED)
    c.showPage()

    c.save()


def main():
    prs = build_pptx()
    prs.save(str(PPTX_PATH))
    draw_pdf()
    print(f"Wrote {PPTX_PATH}")
    print(f"Wrote {PDF_PATH}")
    print(f"Slides: {TOTAL}")


if __name__ == "__main__":
    main()
