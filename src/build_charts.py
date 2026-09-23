"""Exhibits for the bank margin, credit-cost and profit-attribution bridge.

Three charts, each answering a different question, none a restatement of
another:

  01  Where did profit growth come from?      -> profit attribution
  02  Rate cycle or credit cycle?             -> NIM vs credit-cost movement
  03  Did asset quality actually improve?     -> GNPA levels, both quarters

Chart 03 exists to stop chart 01 being over-read. Provisions dominate the
attribution, and a fall in provisions can mean either that borrowers got
better or that the bank simply chose to provide less. Plotting the gross NPA
ratio itself, at level rather than as a change, is what separates those two
readings -- and it is available for all four banks.

Every series is drawn only where the bank discloses it. Coverage gaps are
annotated on the chart rather than dropped silently, because which banks do
not publish a figure is itself a finding.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_CSV = ROOT / "data" / "final" / "margin_bridge.csv"
OUT = ROOT / "outputs" / "charts"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.dpi": 300,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
})

NAVY = "#1a3a5c"
RUST = "#c0522d"
SAGE = "#5c7a5c"
GREY = "#6b6b6b"
SKY = "#4a7c9b"
OCHRE = "#8c6d3f"
SRC = 6.5  # source-annotation font size

# Hue encodes which P&L line; position above/below zero already encodes the
# sign, so the palette deliberately carries no good/bad meaning of its own.
COMPONENTS = [
    ("contrib_nii_pct_of_prior_pat", "Net interest income", NAVY),
    ("contrib_other_income_pct_of_prior_pat", "Other income", SKY),
    ("contrib_opex_pct_of_prior_pat", "Operating expenses", OCHRE),
    ("contrib_provisions_pct_of_prior_pat", "Provisions", RUST),
    ("contrib_tax_pct_of_prior_pat", "Tax", GREY),
]


def _short(bank: str) -> str:
    return bank.replace(" Mahindra Bank", "").replace(" Bank", "")


def chart_profit_attribution(df: pd.DataFrame) -> None:
    """Contributions stack up from zero when positive and down when negative;
    the black dash is the bank's actual reported PAT growth. The two must
    agree -- nim_bridge.check 4 enforces that before this runs."""
    d = df.sort_values("pat_growth_yoy_pct", ascending=False).reset_index(drop=True)
    x = range(len(d))
    fig, ax = plt.subplots(figsize=(9, 5.4))

    pos = [0.0] * len(d)
    neg = [0.0] * len(d)
    for col, label, colour in COMPONENTS:
        vals = d[col].tolist()
        bottoms, heights = [], []
        for i, v in enumerate(vals):
            if v >= 0:
                bottoms.append(pos[i]); pos[i] += v
            else:
                bottoms.append(neg[i] + v); neg[i] += v
            heights.append(abs(v))
        ax.bar(x, heights, bottom=bottoms, width=0.58, color=colour,
               label=label, edgecolor="white", linewidth=0.6)

    # The dash sits inside the stack, so its label needs an opaque backing or
    # it lands on top of a bar segment and neither stays readable.
    for i, v in enumerate(d["pat_growth_yoy_pct"]):
        ax.hlines(v, i - 0.36, i + 0.36, color="black", linewidth=2.2,
                  zorder=5)
        ax.text(i, v, f"{v:+.1f}%", ha="center", va="center", fontsize=9,
                weight="bold", zorder=6,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.6,
                          alpha=0.94))

    ax.axhline(0, color="black", linewidth=0.9)
    ax.set_xticks(list(x))
    ax.set_xticklabels([_short(b) for b in d["bank"]])
    ax.set_ylabel("Contribution to PAT change (pp of Q1 FY26 PAT)")
    ax.set_title(
        "What drove Q1 FY27 profit growth\n"
        "Black dash = reported PAT growth; bars decompose it across the P&L",
        fontsize=11, loc="left", weight="bold")
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([0], [0], color="black", linewidth=2.2))
    labels.append("Reported PAT growth")
    ax.legend(handles, labels, fontsize=8, ncol=6, loc="upper center",
              bbox_to_anchor=(0.5, -0.09), frameon=False)
    # Set the limits from the stack extents rather than leaving it to
    # margins(): the value labels are text artists and skew autoscaling
    # enough to clip the bottom of HDFC's stack.
    top, bottom = max(pos), min(neg)
    pad = (top - bottom) * 0.10
    ax.set_ylim(bottom - pad, top + pad)
    fig.text(0.99, -0.06,
             "Source: standalone Q1 FY26/FY27 results of each bank. Components "
             "reconcile to reported PAT — see data/processed/reconciliation_log.md",
             fontsize=SRC, color=GREY, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "01_profit_attribution.png", bbox_inches="tight")
    plt.close(fig)


def chart_margin_vs_credit_cost(df: pd.DataFrame) -> None:
    """The rate cycle and the credit cycle pulled in opposite directions.
    Both series are in bps so they share one axis honestly."""
    d = df.dropna(subset=["nim_change_bps", "credit_cost_change_bps"]).copy()
    d = d.sort_values("credit_cost_change_bps")
    missing = df[df["nim_change_bps"].isna() | df["credit_cost_change_bps"].isna()]

    x = range(len(d))
    w = 0.34
    fig, ax = plt.subplots(figsize=(8, 5))
    b1 = ax.bar([i - w / 2 for i in x], d["nim_change_bps"], width=w,
                color=NAVY, label="Net interest margin")
    b2 = ax.bar([i + w / 2 for i in x], d["credit_cost_change_bps"], width=w,
                color=RUST, label="Credit cost")

    for bars in (b1, b2):
        for bar in bars:
            v = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2,
                    v - 4 if v < 0 else v + 2, f"{v:+.0f}",
                    ha="center", va="top" if v < 0 else "bottom", fontsize=8.5)

    ax.axhline(0, color="black", linewidth=0.9)
    ax.set_xticks(list(x))
    ax.set_xticklabels([_short(b) for b in d["bank"]])
    ax.set_ylabel("Change Q1 FY26 → Q1 FY27 (bps)")
    ax.set_title(
        "Margins compressed while credit costs fell further\n"
        "Every bank's margin narrowed; every bank's credit cost fell by more basis points",
        fontsize=11, loc="left", weight="bold")
    ax.legend(fontsize=8.5, frameon=False, loc="lower left")
    ax.margins(y=0.22)

    note = ("Credit-cost levels are not comparable across banks — each defines it "
            "differently (see credit_cost_definition in margin_bridge.csv); the "
            "YoY change within a bank is.")
    if len(missing):
        note = (f"{', '.join(_short(b) for b in missing['bank'])} publishes neither "
                f"a NIM nor a credit-cost ratio in this filing and is omitted. ") + note
    fig.text(0.99, -0.055, note, fontsize=SRC, color=GREY, ha="right", wrap=True)
    fig.text(0.99, -0.10, "Source: standalone Q1 FY26/FY27 results of each bank",
             fontsize=SRC, color=GREY, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "02_margin_vs_credit_cost.png", bbox_inches="tight")
    plt.close(fig)


def chart_gnpa_levels(df: pd.DataFrame) -> None:
    """Levels, not changes: the point is that provisions fell against a
    genuinely improving book, and from what starting level."""
    d = df.dropna(subset=["gnpa_q1fy26_pct", "gnpa_q1fy27_pct"]).copy()
    d = d.sort_values("gnpa_q1fy27_pct", ascending=True).reset_index(drop=True)
    y = range(len(d))

    fig, ax = plt.subplots(figsize=(8, 4.2))
    # One fixed column for the bps labels. Hanging each off its own bank's
    # starting value leaves them ragged, which reads as a layout mistake.
    lo = d[["gnpa_q1fy26_pct", "gnpa_q1fy27_pct"]].min().min()
    hi = d[["gnpa_q1fy26_pct", "gnpa_q1fy27_pct"]].max().max()
    label_x = hi + (hi - lo) * 0.16
    for i, r in d.iterrows():
        ax.plot([r["gnpa_q1fy26_pct"], r["gnpa_q1fy27_pct"]], [i, i],
                color=GREY, linewidth=1.4, zorder=1)
        ax.scatter(r["gnpa_q1fy26_pct"], i, s=62, color="white",
                   edgecolor=NAVY, linewidth=1.6, zorder=2)
        ax.scatter(r["gnpa_q1fy27_pct"], i, s=62, color=SAGE, zorder=3)
        ax.text(r["gnpa_q1fy26_pct"] + 0.035, i + 0.16,
                f"{r['gnpa_q1fy26_pct']:.2f}", fontsize=8, color=NAVY)
        ax.text(r["gnpa_q1fy27_pct"] - 0.035, i + 0.16,
                f"{r['gnpa_q1fy27_pct']:.2f}", fontsize=8, color=SAGE,
                ha="right")
        ax.text(label_x, i, f"{r['gnpa_change_bps']:+.0f} bps", fontsize=8.5,
                va="center", ha="left", color=GREY)

    ax.set_yticks(list(y))
    ax.set_yticklabels([_short(b) for b in d["bank"]])
    ax.set_xlabel("Gross NPA ratio (%)")
    ax.set_title(
        "Asset quality improved at every bank\n"
        "Hollow = Q1 FY26, filled = Q1 FY27. Gross NPA throughout — not net NPA",
        fontsize=11, loc="left", weight="bold")
    ax.grid(axis="y", visible=False)
    ax.margins(y=0.22)
    ax.set_xlim(lo - (hi - lo) * 0.19, label_x + (hi - lo) * 0.20)
    fig.text(0.99, -0.06,
             "Source: standalone Q1 FY26/FY27 results of each bank. ICICI's ratio "
             "is gross NPA net of write-off to gross advances, as its filing defines it.",
             fontsize=SRC, color=GREY, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "03_gnpa_levels.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.png"):
        stale.unlink()

    df = pd.read_csv(BRIDGE_CSV)
    chart_profit_attribution(df)
    chart_margin_vs_credit_cost(df)
    chart_gnpa_levels(df)

    print("Charts written to", OUT)
    for f in sorted(OUT.glob("*.png")):
        print(" -", f.name)
