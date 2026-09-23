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
    "h1": ParagraphStyle("h1", fontName="DejaVuSans-Bold", fontSize=14, leading=18, textColor=NAVY, spaceBefore=16, spaceAfter=8, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="DejaVuSans-Bold", fontSize=11.5, leading=15, textColor=NAVY, spaceBefore=10, spaceAfter=6, keepWithNext=1),
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


def fmt_pp(v) -> str:
    """Attribution contributions, in percentage points of prior-year PAT."""
    return f"{v:+.1f}" if pd.notna(v) else "—"


def build() -> None:
    df = pd.read_csv(ROOT / "data" / "final" / "margin_bridge.csv")
    df = df.sort_values("pat_growth_yoy_pct", ascending=False)

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                             topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    story = []

    story.append(P("Bank Margin &amp; Credit-Cost Bridge, Q1 FY27 vs Q1 FY26", "title"))
    story.append(P("HDFC Bank · ICICI Bank · Axis Bank · Kotak Mahindra Bank — where profit growth "
                    "actually came from in the quarter ended 30 June 2026, all four on a standalone basis.", "subtitle"))
    story.append(P("Shaswat Sharma &nbsp;·&nbsp; github.com/theshaswat &nbsp;·&nbsp; September 2026", "small"))
    story.append(Spacer(1, 6))

    story.append(P("The question", "h1"))
    story.append(P(
        "All four banks grew profit in the June 2026 quarter. That single number hides the fact "
        "that they got there in very different ways. This memo asks how much of each bank\u2019s "
        "profit growth came from the lending business widening, and how much came from provisioning "
        "less against it \u2014 because only one of those is repeatable.", "body"))
    story.append(P(
        "Everything below is built from the four banks\u2019 own standalone results filings. Every "
        "figure carries a page citation in <font name='DejaVuSans-Oblique'>data/final/verified_inputs.csv"
        "</font>, and four reconciliation checks have to pass before any comparison in this memo is "
        "computed at all.", "body"))

    story.append(P("What the numbers say", "h1"))
    story.append(P(
        "Every bank\u2019s net interest margin compressed. Every bank\u2019s profit grew. The line "
        "that reconciles those two facts is provisions.", "body"))

    hdr = ["Bank", "Net interest income", "Other income", "Operating expenses",
           "Provisions", "Tax", "Reported PAT growth"]
    attrib = [[Paragraph(h, styles["th"]) for h in hdr]]
    for _, r in df.iterrows():
        attrib.append([
            r["bank"],
            fmt_pp(r["contrib_nii_pct_of_prior_pat"]),
            fmt_pp(r["contrib_other_income_pct_of_prior_pat"]),
            fmt_pp(r["contrib_opex_pct_of_prior_pat"]),
            fmt_pp(r["contrib_provisions_pct_of_prior_pat"]),
            fmt_pp(r["contrib_tax_pct_of_prior_pat"]),
            fmt_pct(r["pat_growth_yoy_pct"]),
        ])
    story.append(KeepTogether([
        build_table(attrib, [4.1 * cm, 2.1 * cm, 1.9 * cm, 2.2 * cm, 2.4 * cm, 1.5 * cm, 2.8 * cm]),
        P("Each component\u2019s contribution to the change in profit, in percentage points of the "
          "prior-year quarter\u2019s PAT. The five contributions sum to the last column \u2014 "
          "reconciliation check 4 enforces that against each bank\u2019s reported figure.", "small"),
    ]))

    story.append(P(
        "Read the provisions column against the last one. Axis grew profit 22.5%, and the fall in "
        "provisions alone contributed 29.7 points of that \u2014 more than the entire increase. "
        "Strip provisions and tax out and the operating business contributed 2.5 points. ICICI is "
        "the opposite case: 12.8 of its 15.9 points came from operations and 3.1 from the provision "
        "and tax lines. On the evidence in these four filings, ICICI\u2019s profit growth is the "
        "least dependent on the credit cycle staying benign, and Axis\u2019s is the most.", "body"))

    story.append(KeepTogether([
        Image(str(CHARTS / "01_profit_attribution.png"), width=15.5 * cm, height=9.3 * cm),
        P("Figure 1. The same decomposition. Bars stack above and below zero by sign; the black "
          "dash is each bank\u2019s reported PAT growth.", "caption"),
    ]))

    story.append(P("How these figures are checked", "h1"))
    story.append(P(
        "Four checks run in <font name='DejaVuSans-Oblique'>src/nim_bridge.py</font> before the "
        "bridge is written, and it is not written unless all four pass. Each is capable of failing "
        "on a transcription error \u2014 none of them passes by construction, which is the point:", "body"))
    story.append(P(
        "1. <b>NII arithmetic tie-out.</b> Interest earned less interest expended equals printed NII. "
        "Runs only for banks publishing both the split and their own NII line \u2014 Axis alone.", "bullet"))
    story.append(P(
        "2. <b>Computed growth against the bank\u2019s own published growth.</b> Growth is recomputed "
        "from the extracted absolutes and compared with the percentage the bank itself printed, across "
        "eight bank-metric pairs. An error in either quarter breaks it.", "bullet"))
    story.append(P(
        "3. <b>P&amp;L walk.</b> NII plus other income, less opex, provisions and tax, equals reported "
        "PAT \u2014 all four banks, both quarters. Tolerances are derived from each bank\u2019s own "
        "reporting precision rather than chosen.", "bullet"))
    story.append(P(
        "4. <b>Attribution closes.</b> The five contributions sum back to the reported change in "
        "profit, within the same bounded rounding.", "bullet"))
    story.append(P(
        "One check is deliberately not run. ICICI prints no net interest income line anywhere in its "
        "filing, so its NII is derived here as interest earned less interest expended. Running the "
        "arithmetic tie-out on a figure derived from that same arithmetic would pass every time and "
        "prove nothing, so ICICI is flagged <font name='DejaVuSans-Oblique'>derived</font> and "
        "excluded from check 1. It is still covered by checks 3 and 4.", "body"))

    story.append(P("Bank by bank", "h1"))

    story.append(KeepTogether([
        P("Axis Bank \u2014 profit growth almost entirely from the provision line", "h2"),
        P(
            "NII grew 8.0% (interest income \u20b931,064 Cr \u2192 \u20b933,986 Cr, interest "
            "expended \u20b917,504 Cr \u2192 \u20b919,340 Cr, tie-out exact in both quarters) while "
            "PAT grew 22.5%. The gap is not a mystery: provisions fell from \u20b93,948 Cr to "
            "\u20b92,223 Cr, a 43.7% reduction on the same page of the same deck, contributing 29.7 "
            "points of profit growth against a total of 22.5. Other income fell 7.2% and operating "
            "expenses rose 4.5%, which together took 16.2 points back off. Axis also shows the largest "
            "margin compression in the set at \u221234 bps and the largest credit-cost improvement at "
            "\u221275 bps. Both of those point the same way: this is a quarter where the credit cycle, "
            "not the lending business, carried the result.", "body"),
    ]))

    story.append(KeepTogether([
        P("ICICI Bank \u2014 the most core-driven growth of the four", "h2"),
        P(
            "NII grew 12.7%, the fastest in the set, contributing 21.5 points against 15.9% PAT growth. "
            "Provisions contributed only 4.3 points, the smallest reliance on that line of any bank "
            "here. Operating expenses grew 10.4% and took 9.2 points back. ICICI also posted the "
            "largest asset-quality improvement, gross NPA down 33 bps from the highest starting level "
            "in the set at 1.75%. Two things it does not publish: a net interest margin and a "
            "credit-cost ratio. Those cells are empty rather than sourced from elsewhere, and ICICI is "
            "omitted from Figure 2 for that reason. Its results are used on a standalone basis \u2014 "
            "the consolidated figures include large insurance subsidiaries and would not be comparable "
            "with the other three.", "body"),
    ]))

    story.append(KeepTogether([
        P("Kotak Mahindra Bank \u2014 fastest profit growth, and the most balanced", "h2"),
        P(
            "PAT grew 25.6%, the fastest of the four, and the split behind it is more even than the "
            "headline suggests: 20.4 points from NII, 7.9 from other income, 16.5 from lower "
            "provisions, against 11.0 points of operating-expense growth and 8.1 of tax. Credit cost "
            "fell 47 bps and gross NPA fell 30 bps to 1.18%, the second-lowest level in this set, "
            "just above HDFC\u2019s 1.17%. Worth stating plainly: Kotak grew profit both by lending more and by "
            "setting aside less, and one year-on-year comparison cannot say how much of the second "
            "part persists. Kotak\u2019s Q1 FY26 deck downloaded with a corrupted file structure and "
            "was dropped \u2014 both quarters here come from the Q1 FY27 deck\u2019s own comparative "
            "columns, not a repaired file.", "body"),
    ]))

    story.append(KeepTogether([
        P("HDFC Bank \u2014 the headline number most likely to be misread", "h2"),
        P(
            "PAT grew 5.0%, by far the slowest of the four, and the reason is almost entirely a base "
            "effect rather than anything about the current quarter. Other income fell 41% year on year, "
            "from \u20b921,730 Cr to \u20b912,820 Cr, because the June 2025 quarter contained a "
            "one-time gain on the partial divestment of HDB Financial Services. That drop costs 49.1 "
            "points of profit growth. Against it sits an \u20b911,380 Cr fall in provisions worth 62.7 "
            "points. Neither side is a run-rate, and the 5.0% headline is the residue of two large "
            "one-offs pulling in opposite directions.", "body"),
        P(
            "The underlying business is steadier than the headline: NII grew 6.6%, operating expenses "
            "grew only 4.4%, gross NPA fell 23 bps to 1.17%, and the margin compressed 9 bps \u2014 "
            "the smallest compression in the set, not the largest. An earlier draft of this memo "
            "described HDFC as the bank with margin under the most pressure. That was wrong, and it "
            "came from reading the profit line without decomposing it first.", "body"),
    ]))

    story.append(PageBreak())

    story.append(P("Margins and asset quality", "h1"))
    story.append(P(
        "Net interest income grew at every bank while the margin narrowed at every bank that "
        "publishes one. The books grew faster than the margin compressed. Credit costs fell by more "
        "basis points than margins did at all three banks disclosing both.", "body"))

    story.append(KeepTogether([
        Image(str(CHARTS / "02_margin_vs_credit_cost.png"), width=14.5 * cm, height=9.1 * cm),
        P("Figure 2. NIM and credit-cost movement. Credit-cost <i>levels</i> are not comparable "
          "across banks \u2014 each defines the ratio differently \u2014 so only the change is "
          "plotted. ICICI publishes neither ratio and is omitted.", "caption"),
    ]))

    story.append(KeepTogether([
        Image(str(CHARTS / "03_gnpa_levels.png"), width=15.5 * cm, height=8.1 * cm),
        P("Figure 3. Gross NPA ratio at both dates. Gross throughout \u2014 net NPA is a different, "
          "lower series and is kept in a separate column.", "caption"),
    ]))

    story.append(P(
        "Figure 3 is what stops Figure 1 being over-read. Provisions dominate the attribution, and a "
        "fall in provisions can mean either that borrowers improved or that the bank chose to provide "
        "less. Gross NPA fell at all four banks, which supports the first reading. It does not settle "
        "it: a bank running down a buffer built in an earlier cycle and a bank whose borrowers are "
        "genuinely repaying better both look like this for several quarters. Separating them needs "
        "provision coverage and a slippage series across more quarters than this covers.", "body"))

    story.append(KeepTogether([
        P("What this deliberately doesn\u2019t do", "h1"),
        P(
            "This is not a rate/volume/mix decomposition. That was the original scope and it was cut "
            "for a specific reason: it needs yield on assets and cost of funds for both periods, and "
            "HDFC and Kotak publish those only as labels inside chart images with no reliable "
            "position-to-label mapping available to text extraction. A decomposition built on two "
            "banks\u2019 real numbers and two banks\u2019 guessed ones would look complete and be "
            "half-fabricated. The P&amp;L attribution used instead answers a coarser question, on "
            "figures all four banks actually print.", "body"),
        P(
            "It is also not a panel regression. Four banks and two quarters is eight observations. "
            "There are no p-values, no clustered standard errors and no bootstrap anywhere in this "
            "project. <font name='DejaVuSans-Oblique'>indfin.stats.wild_cluster</font> exists for a "
            "project that has a panel; running it here would produce a statistic with nothing behind "
            "it. The full list is in LIMITATIONS.md.", "body"),
    ]))

    story.append(Spacer(1, 10))
    story.append(P(
        "Data: Q1 FY26 and Q1 FY27 standalone results filings of each bank (URLs and SHA-256 hashes "
        "in data/raw/source_manifest.md). Code: src/nim_bridge.py, using the indfin library\u2019s "
        "reconciliation modules. Reconciliation results: data/processed/reconciliation_log.md. "
        "Repository: github.com/theshaswat/bank-nim-credit-cost-bridge.", "small"))

    doc.build(story)
    print(f"Written: {OUT_PDF}")


if __name__ == "__main__":
    build()
