"""Methodology + findings memo, as a PDF. Registers DejaVu Sans (via
matplotlib's bundled copy) so the ₹ glyph renders correctly."""
from __future__ import annotations

from pathlib import Path

import matplotlib
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "outputs" / "charts"
OUT_PDF = ROOT / "reports" / "methodology_memo.pdf"

mpl_fonts = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DejaVuSans", str(mpl_fonts / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(mpl_fonts / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", str(mpl_fonts / "DejaVuSans-Oblique.ttf")))

NAVY = colors.HexColor("#1a3a5c")
GREY = colors.HexColor("#6b6b6b")

styles = {
    "title": ParagraphStyle("title", fontName="DejaVuSans-Bold", fontSize=20, leading=24, textColor=NAVY, spaceAfter=4),
    "subtitle": ParagraphStyle("subtitle", fontName="DejaVuSans-Oblique", fontSize=10.5, leading=14, textColor=GREY, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName="DejaVuSans-Bold", fontSize=14, leading=18, textColor=NAVY, spaceBefore=16, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="DejaVuSans-Bold", fontSize=11.5, leading=15, textColor=NAVY, spaceBefore=10, spaceAfter=6),
    "body": ParagraphStyle("body", fontName="DejaVuSans", fontSize=10, leading=15, spaceAfter=8),
    "small": ParagraphStyle("small", fontName="DejaVuSans", fontSize=8, leading=11, textColor=GREY, spaceAfter=6),
    "caption": ParagraphStyle("caption", fontName="DejaVuSans-Oblique", fontSize=8.5, leading=11, textColor=GREY, spaceAfter=14, alignment=1),
    "th": ParagraphStyle("th", fontName="DejaVuSans-Bold", fontSize=8.5, leading=10.5, textColor=colors.white, alignment=1),
    "bullet": ParagraphStyle("bullet", fontName="DejaVuSans", fontSize=10, leading=15, spaceAfter=6, leftIndent=10, bulletIndent=0),
}


def P(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, styles[style])


def build_table(data, col_widths, header=True) -> Table:
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    cmds = [
        ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        cmds += [
            ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]
    t.setStyle(TableStyle(cmds))
    return t


def fmt_pct(v) -> str:
    return f"{v:+.1f}%" if pd.notna(v) else "—"


def fmt_bps(v) -> str:
    return f"{v:+.0f} bps" if pd.notna(v) else "—"


def build() -> None:
    df = pd.read_csv(ROOT / "data" / "final" / "margin_bridge.csv")
    df = df.sort_values("pat_growth_yoy_pct", ascending=False)

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                             topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    story = []

    story.append(P("Bank Margin &amp; Profitability Bridge, Q1 FY27 vs Q1 FY26", "title"))
    story.append(P("HDFC Bank · Axis Bank · ICICI Bank · Kotak Mahindra Bank — what actually "
                    "moved profit, margin, and asset quality year-on-year for the quarter ended 30-Jun-2026.", "subtitle"))
    story.append(P("Shaswat Sharma &nbsp;·&nbsp; github.com/theshaswat &nbsp;·&nbsp; September 2026", "small"))
    story.append(Spacer(1, 6))

    story.append(P("The question", "h1"))
    story.append(P(
        "Four private-sector banks reported Q1 FY27 (quarter ended 30-Jun-2026) results this year, "
        "each with a headline profit growth number. This bridge asks what's underneath that one "
        "number for each bank — did profit grow because the core lending business actually widened, "
        "or because credit costs fell, or some mix of both — using only the figures each bank actually "
        "discloses, not a model that assumes they all disclose the same thing.", "body"))

    story.append(P("Method, and why it isn't one model across all four", "h1"))
    story.append(P(
        "The original plan for this project was a three-factor rate/volume/mix decomposition of net "
        "interest income across a full quarterly panel. That plan didn't survive contact with the "
        "actual disclosures. Axis and ICICI publish a clean Interest Income / Interest Expended / NII "
        "table; HDFC and Kotak instead publish average balances and a headline NIM% directly, with "
        "yield-on-assets and cost-of-funds shown only as chart labels that don't map unambiguously "
        "to values through plain-text PDF extraction. Forcing one model across all four would have "
        "meant guessing at two of the four banks' numbers to make the model run. Instead, this bridge "
        "computes what each bank's own disclosure actually supports:", "body"))
    story.append(P(
        "• <b>NII growth (YoY)</b> — Axis, ICICI: reconciled via Interest Income − Interest Expended = "
        "NII, tied to each bank's own reported NII figure (see <font name='DejaVuSans-Oblique'>"
        "data/processed/reconciliation_log.md</font> — exact match, all four quarters).", "bullet"))
    story.append(P(
        "• <b>NIM% and GNPA% movement (YoY, bps)</b> — HDFC, Kotak: both disclose headline NIM% and "
        "GNPA% directly for both quarters.", "bullet"))
    story.append(P(
        "• <b>PAT growth (YoY)</b> and <b>average advances growth (YoY)</b> — computed for every bank "
        "where disclosed.", "bullet"))
    story.append(P(
        "One basis note worth flagging rather than glossing over: ICICI's two source decks are "
        "different document types — the Q1FY26 file is a full investor presentation, the Q1FY27 file "
        "is the shorter regulatory results filing. Both carry the same results-table structure and "
        "both tie out exactly, but it's a genuine format asymmetry, not an oversight.", "body"))

    header_labels = ["Bank", "PAT Growth\nYoY", "NII Growth\nYoY", "NIM Δ", "GNPA% Δ", "Credit Cost Δ"]
    table_data = [[Paragraph(h.replace("\n", "<br/>"), styles["th"]) for h in header_labels]]
    for _, r in df.iterrows():
        table_data.append([
            r["bank"], fmt_pct(r["pat_growth_yoy_pct"]), fmt_pct(r["nii_growth_yoy_pct"]),
            fmt_bps(r["nim_change_bps"]), fmt_bps(r["gnpa_change_bps"]), fmt_bps(r["credit_cost_change_bps"]),
        ])
    story.append(KeepTogether([
        P("What moved, bank by bank", "h1"),
        build_table(table_data, [3.8 * cm, 2.5 * cm, 2.5 * cm, 2.1 * cm, 2.3 * cm, 2.6 * cm]),
        P("Blank cells are not zeros — they mean that bank doesn't disclose that figure in a form this "
          "project could verify, and nothing was filled in to complete the row.", "small"),
    ]))

    story.append(KeepTogether([
        Image(str(CHARTS / "01_pat_growth_yoy.png"), width=15 * cm, height=9.4 * cm),
        P("Figure 1. Q1 FY27 PAT growth vs Q1 FY26, all four banks.", "caption"),
    ]))

    story.append(PageBreak())

    story.append(P("Bank by bank", "h1"))

    story.append(KeepTogether([
        P("Kotak Mahindra Bank — fastest profit growth, and the only bank with a complete row", "h2"),
        P(
            "Kotak's PAT grew 25.6% YoY, the fastest of the four, and it's the one bank in this set "
            "disclosing NIM, GNPA%, and credit cost movement all in one place — NIM down 12 bps, GNPA% "
            "down 7 bps, credit cost down a sharp 47 bps, alongside 15.2% average-advances growth. Falling "
            "credit cost doing a lot of the work here is worth noting plainly: a bank can grow profit by "
            "lending more, or by setting aside less for expected losses, and this quarter Kotak did "
            "both. Whether the credit-cost decline holds up depends on how the underlying book performs "
            "next year, which this single YoY comparison can't tell you. Also worth remembering: Kotak's "
            "Q1FY26 deck downloaded with a corrupted file structure this session and had to be dropped — "
            "every Kotak figure here, both quarters, comes from the Q1FY27 deck's own comparative "
            "columns instead, not a repaired or reconstructed file.", "body"),
    ]))

    story.append(KeepTogether([
        P("Axis Bank — NII growing slower than profit", "h2"),
        P(
            "Axis's NII grew 8.0% YoY (Interest Income ₹31,064 Cr → ₹33,986 Cr, Interest Expended "
            "₹17,504 Cr → ₹19,340 Cr, both ties confirmed against reported NII), while PAT grew 22.5% "
            "— profit growing meaningfully faster than the core lending margin. That gap has to be "
            "explained by something below NII: fee income, treasury gains, provisioning, or opex "
            "discipline. This project doesn't have Axis's full P&amp;L broken down that far, so it's stated "
            "as an open question rather than an assumed answer — NII growth alone doesn't account for "
            "the PAT growth, and this memo isn't going to guess which of the other lines did.", "body"),
    ]))

    story.append(KeepTogether([
        P("ICICI Bank — steadiest of the four", "h2"),
        P(
            "NII grew 12.3% YoY (the fastest NII growth in this set), PAT grew 13.9% — the two numbers "
            "track each other closely, unlike Axis. That's a simpler story than the other three banks "
            "tell: core lending income grew, and profit grew roughly in line with it. ICICI doesn't "
            "disclose NIM%, GNPA%, or credit cost in the same table structure used here for HDFC and "
            "Kotak, so this bank's row in the summary table is deliberately incomplete rather than "
            "padded with a number from a different source.", "body"),
    ]))

    story.append(KeepTogether([
        P("HDFC Bank — slowest profit growth, and margin under the most pressure", "h2"),
        P(
            "HDFC's PAT grew just 4.9% YoY, by far the slowest of the four, alongside the largest NIM "
            "compression in this set at −9 bps. Average advances still grew 10.8%, so this isn't a "
            "lending slowdown — it's a bank growing its book while earning less on it, and the profit "
            "line shows that squeeze directly. The one genuine bright spot: GNPA% fell 23 bps, the "
            "largest asset-quality improvement of the four banks that disclose it, which at least says "
            "the margin pressure isn't coming from a deteriorating loan book. HDFC's decks also carry a "
            "yield-on-assets / cost-of-funds chart that would explain the NIM compression directly — "
            "rate side or funding-cost side — but the chart's labels don't map unambiguously to values "
            "through plain-text extraction, so this memo doesn't claim a number it can't stand behind.", "body"),
    ]))

    story.append(KeepTogether([
        Image(str(CHARTS / "02_nii_growth_yoy.png"), width=13.5 * cm, height=9.5 * cm),
        P("Figure 2. NII growth YoY — Axis and ICICI only, the two banks whose Interest Income/Expended split ties out to reported NII.", "caption"),
    ]))

    story.append(PageBreak())

    story.append(KeepTogether([
        Image(str(CHARTS / "03_nim_gnpa_movement.png"), width=16 * cm, height=8.8 * cm),
        P("Figure 3. NIM% and GNPA% movement YoY — HDFC and Kotak only, the two banks disclosing both headline ratios directly for both quarters.", "caption"),
    ]))

    story.append(KeepTogether([
        P("What this deliberately doesn't do", "h1"),
        P(
            "This isn't a 12-quarter panel and it isn't a rate/volume/mix decomposition — both were the "
            "original scope, and both were cut once the actual disclosures didn't support them honestly "
            "across all four banks (see the Method section above). It also doesn't attempt a wild-cluster "
            "bootstrap or any panel-regression inference; with 4 banks and 2 quarters there's no panel "
            "to run inference on, and pretending otherwise would produce a p-value with no meaning behind "
            "it. See LIMITATIONS.md for the complete list.", "body"),
    ]))

    story.append(Spacer(1, 10))
    story.append(P(
        "Data: bank Q1 FY26 / Q1 FY27 investor presentations and results filings (see "
        "data/raw/source_manifest.md for URLs and file hashes). Code: src/nim_bridge.py, using the "
        "indfin library's NII reconciliation module. Repository: "
        "github.com/theshaswat/bank-nim-credit-cost-bridge.", "small"))

    doc.build(story)
    print(f"Written: {OUT_PDF}")


if __name__ == "__main__":
    build()
