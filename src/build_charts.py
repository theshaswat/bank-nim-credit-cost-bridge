"""Exhibits for the bank margin & profitability bridge. Three charts, no
overlap, each built only from the metrics actually disclosed by that bank
(see margin_bridge.csv — NII growth only exists for Axis/ICICI, NIM/GNPA
movement only for HDFC/Kotak; nothing here is filled in or estimated)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

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


def chart_pat_growth(df: pd.DataFrame) -> None:
    d = df.sort_values("pat_growth_yoy_pct", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(d["bank"], d["pat_growth_yoy_pct"], color=NAVY)
    ax.set_ylabel("PAT growth, Q1 FY26 → Q1 FY27, YoY %")
    ax.set_title("Q1 FY27 Profit Growth vs Q1 FY26 (YoY)", fontsize=11, loc="left", weight="bold")
    for bar, val in zip(bars, d["pat_growth_yoy_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4, f"{val:+.1f}%", ha="center", fontsize=9)
    ax.margins(y=0.15)
    plt.setp(ax.get_xticklabels(), rotation=12, ha="right")
    ax.text(0.99, 0.02, "Source: bank Q1 FY26/FY27 investor decks, PAT reconciled to reported figures",
             transform=ax.transAxes, fontsize=6.5, color=GREY, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "01_pat_growth_yoy.png", bbox_inches="tight")
    plt.close(fig)


def chart_nii_growth(df: pd.DataFrame) -> None:
    d = df.dropna(subset=["nii_growth_yoy_pct"]).sort_values("nii_growth_yoy_pct", ascending=False)
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    bars = ax.bar(d["bank"], d["nii_growth_yoy_pct"], color=SAGE, width=0.5)
    ax.set_ylabel("NII growth, Q1 FY26 → Q1 FY27, YoY %")
    ax.set_title("Net Interest Income Growth (YoY)\nOnly banks disclosing Interest Income/Expended separately — NII tied out via indfin.check_nii",
                  fontsize=10, loc="left", weight="bold")
    for bar, val in zip(bars, d["nii_growth_yoy_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2, f"{val:+.1f}%", ha="center", fontsize=9)
    ax.margins(y=0.2)
    fig.text(0.99, -0.02, "Source: bank Q1 decks — indfin.reconcile.nii tie-out log in data/processed/",
              fontsize=6.5, color=GREY, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "02_nii_growth_yoy.png", bbox_inches="tight")
    plt.close(fig)


def chart_nim_gnpa_movement(df: pd.DataFrame) -> None:
    d = df.dropna(subset=["nim_change_bps"]).sort_values("bank")
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.5))

    ax = axes[0]
    colors = [SAGE if v < 0 else RUST for v in d["nim_change_bps"]]
    bars = ax.bar(d["bank"], d["nim_change_bps"], color=colors, width=0.5)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("bps change, Q1 FY26 → Q1 FY27")
    ax.set_title("NIM movement (YoY)", fontsize=10, loc="left", weight="bold")
    for bar, val in zip(bars, d["nim_change_bps"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + (1 if val >= 0 else -3),
                 f"{val:+.0f} bps", ha="center", fontsize=9)
    ax.margins(y=0.3)

    ax2 = axes[1]
    d2 = df.dropna(subset=["gnpa_change_bps"]).sort_values("bank")
    colors2 = [SAGE if v < 0 else RUST for v in d2["gnpa_change_bps"]]
    bars2 = ax2.bar(d2["bank"], d2["gnpa_change_bps"], color=colors2, width=0.5)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_title("GNPA% movement (YoY)\nnegative = improving asset quality", fontsize=10, loc="left", weight="bold")
    for bar, val in zip(bars2, d2["gnpa_change_bps"]):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + (1 if val >= 0 else -3),
                  f"{val:+.0f} bps", ha="center", fontsize=9)
    ax2.margins(y=0.3)

    fig.suptitle("Margin & Asset-Quality Movement — banks disclosing both quarters' figures directly",
                  fontsize=10.5, x=0.02, ha="left", y=1.03)
    fig.text(0.99, -0.02, "Source: bank Q1 FY26/FY27 investor decks, headline NIM%/GNPA% as reported",
              fontsize=6.5, color=GREY, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "03_nim_gnpa_movement.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(BRIDGE_CSV)

    chart_pat_growth(df)
    chart_nii_growth(df)
    chart_nim_gnpa_movement(df)

    print("Charts written to", OUT)
    for f in sorted(OUT.glob("*.png")):
        print(" -", f.name)
