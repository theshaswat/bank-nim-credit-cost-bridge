"""YoY margin & profitability bridge across the 4-bank panel.

Honest methodology note (stated here, and again in the memo): the four
banks' investor disclosures are not uniform enough to support one forced
three-factor rate/volume/mix regression across all of them — Axis and
ICICI disclose clean Interest Income/Expended tables (from which NII ties
out exactly); HDFC and Kotak disclose average balances and headline NIM%
directly, not a rate/volume split. Rather than force a common model onto
incompatible disclosures (or silently drop the two that don't fit), this
computes what each bank's own numbers actually support — NII growth where
the interest income/expense split exists, NIM/credit-cost movement where
it's stated directly — and presents them side by side as a comparative
bridge, not a single regression output.

Every input in data/final/verified_inputs.csv is hand-extracted from a
specific, cited page — see source_page_note and
data/raw/source_manifest_additions.csv for hashes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "indfin"))
from indfin.reconcile.nii import check_nii  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = ROOT / "data" / "final" / "verified_inputs.csv"
OUTPUT_CSV = ROOT / "data" / "final" / "margin_bridge.csv"
RECON_LOG = ROOT / "data" / "processed" / "reconciliation_log.md"


def reconcile_nii(df: pd.DataFrame) -> list[str]:
    lines = ["# Reconciliation Log — Bank Margin & Profitability Bridge", "",
             "NII tie-out run only where interest income AND interest "
             "expended are both disclosed (Axis, ICICI). HDFC and Kotak "
             "disclose headline NIM/average balances directly, not a "
             "reportable NII figure to tie against — noted, not silently "
             "skipped.", ""]
    for _, row in df.dropna(subset=["interest_income", "interest_expended", "nii_reported"]).iterrows():
        r = check_nii(
            bank=f"{row['bank']} {row['quarter']}", period=row["quarter"],
            interest_earned=row["interest_income"],
            interest_expended=row["interest_expended"],
            nii_reported=row["nii_reported"],
        )
        status = "PASS" if r.passed else "FAIL"
        lines.append(f"- **{row['bank']} {row['quarter']}** NII tie-out: {status} "
                      f"(computed {r.nii_computed:,.2f} vs reported {r.nii_reported:,.2f}, "
                      f"diff {r.diff:.2f})")
    RECON_LOG.write_text("\n".join(lines))
    return lines


def build_bridge(df: pd.DataFrame) -> pd.DataFrame:
    q27 = df[df["quarter"] == "Q1 FY27"].set_index("bank")
    q26 = df[df["quarter"] == "Q1 FY26"].set_index("bank")

    rows = []
    for bank in q27.index:
        r27, r26 = q27.loc[bank], q26.loc[bank]
        nii_growth = None
        if pd.notna(r27.get("nii_reported")) and pd.notna(r26.get("nii_reported")):
            nii_growth = (r27["nii_reported"] / r26["nii_reported"] - 1) * 100
        pat_growth = (r27["pat"] / r26["pat"] - 1) * 100
        nim_change_bps = None
        if pd.notna(r27.get("nim_pct")) and pd.notna(r26.get("nim_pct")):
            nim_change_bps = (r27["nim_pct"] - r26["nim_pct"]) * 100
        gnpa_change_bps = None
        if pd.notna(r27.get("gnpa_pct")) and pd.notna(r26.get("gnpa_pct")):
            gnpa_change_bps = (r27["gnpa_pct"] - r26["gnpa_pct"]) * 100
        credit_cost_change_bps = None
        if pd.notna(r27.get("credit_cost_pct")) and pd.notna(r26.get("credit_cost_pct")):
            credit_cost_change_bps = (r27["credit_cost_pct"] - r26["credit_cost_pct"]) * 100
        adv_growth = None
        if pd.notna(r27.get("avg_advances")) and pd.notna(r26.get("avg_advances")):
            adv_growth = (r27["avg_advances"] / r26["avg_advances"] - 1) * 100

        rows.append({
            "bank": bank,
            "nii_growth_yoy_pct": nii_growth,
            "advances_growth_yoy_pct": adv_growth,
            "pat_growth_yoy_pct": pat_growth,
            "nim_change_bps": nim_change_bps,
            "gnpa_change_bps": gnpa_change_bps,
            "credit_cost_change_bps": credit_cost_change_bps,
            "pat_q1fy27_cr": r27["pat"],
            "pat_q1fy26_cr": r26["pat"],
        })
    result = pd.DataFrame(rows).sort_values("pat_growth_yoy_pct", ascending=False)
    return result


if __name__ == "__main__":
    df = pd.read_csv(INPUT_CSV)
    log_lines = reconcile_nii(df)
    print("\n".join(log_lines))
    print()

    bridge = build_bridge(df)
    print(bridge.to_string(index=False))
    bridge.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWritten: {OUTPUT_CSV}")
