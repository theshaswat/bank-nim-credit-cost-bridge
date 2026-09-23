"""YoY margin, credit-cost and profit-attribution bridge across the 4-bank panel.

All four banks are compared on a STANDALONE basis (ICICI's consolidated
results include large insurance subsidiaries and are not comparable with the
other three banks' standalone figures; its standalone results are in the same
filing and are what this project uses).

Four independent checks run before the bridge is written. Each one is
capable of failing on a transcription error — none of them passes by
construction:

1. NII arithmetic tie-out -- only for banks that print BOTH the interest
   income/expended split AND their own NII line. That is Axis alone. ICICI
   prints the split but no NII line, so its NII is derived here and flagged
   `derived` in verified_inputs.csv: checking a derived figure against its own
   definition would pass by definition and prove nothing, so it is not run.

2. Stated-vs-computed growth -- every bank that publishes its own YoY growth
   percentage has that figure recorded in data/raw/bank_stated_yoy.csv. This
   recomputes growth from the extracted absolute figures and compares against
   what the bank itself published. A transcription error in either period's
   figure breaks it.

3. P&L walk -- NII + other income - opex - provisions - tax must equal
   reported PAT, for all four banks in both quarters. This is the check that
   makes the attribution in build_bridge() trustworthy: if the five components
   did not sum to the reported bottom line, decomposing the change in that
   bottom line across them would be meaningless.

Only after all three pass does the module compute the attribution: how much of
each bank's YoY change in profit came from net interest income, from other
income, from operating expenses, from provisions, and from tax.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from indfin.reconcile.nii import check_nii

ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = ROOT / "data" / "final" / "verified_inputs.csv"
STATED_CSV = ROOT / "data" / "raw" / "bank_stated_yoy.csv"
OUTPUT_CSV = ROOT / "data" / "final" / "margin_bridge.csv"
RECON_LOG = ROOT / "data" / "processed" / "reconciliation_log.md"

Q_PRIOR, Q_CURRENT = "Q1 FY26", "Q1 FY27"

# Each bank's smallest published unit, in Rs Crore. HDFC prints its standalone
# income statement in Rs billion to one decimal (0.1bn = Rs 10 Cr); Axis and
# Kotak print whole Rs Crore; ICICI prints Rs Crore to two decimals. A figure
# rounded to unit u carries up to u/2 of error, and the P&L walk sums five such
# figures, so its tolerance is 5 * u/2. These are derived from what each bank
# publishes, not chosen to make the check pass.
REPORTING_UNIT_CR = {
    "HDFC Bank": 10.0,
    "Axis Bank": 1.0,
    "Kotak Mahindra Bank": 1.0,
    "ICICI Bank": 0.01,
}
WALK_LINES = 5


def walk_tolerance(bank: str) -> float:
    return WALK_LINES * REPORTING_UNIT_CR[bank] / 2


def growth(curr: float, prior: float) -> float | None:
    if pd.isna(curr) or pd.isna(prior) or prior == 0:
        return None
    return (curr / prior - 1) * 100


def delta_bps(curr: float, prior: float) -> float | None:
    if pd.isna(curr) or pd.isna(prior):
        return None
    return round((curr - prior) * 100, 1)


def check_nii_tieout(df: pd.DataFrame) -> tuple[list[str], bool, list[dict]]:
    lines = [
        "## 1. NII arithmetic tie-out",
        "",
        "Run only where a bank prints both the interest income/expended split "
        "and its own NII line, so the check is capable of failing.",
        "",
    ]
    ok = True
    recs: list[dict] = []
    tieable = df[(df["nii_source"] == "reported")
                 & df["interest_income_cr"].notna()
                 & df["interest_expended_cr"].notna()]
    for _, r in tieable.iterrows():
        res = check_nii(
            bank=f"{r['bank']} {r['quarter']}", period=r["quarter"],
            interest_earned=r["interest_income_cr"],
            interest_expended=r["interest_expended_cr"],
            nii_reported=r["nii_cr"],
        )
        ok &= res.passed
        lines.append(
            f"- **{r['bank']} {r['quarter']}**: {'PASS' if res.passed else 'FAIL'} — "
            f"{r['interest_income_cr']:,.2f} − {r['interest_expended_cr']:,.2f} = "
            f"{res.nii_computed:,.2f} vs printed {res.nii_reported:,.2f} "
            f"(diff {res.diff:.2f})"
        )
        recs.append({
            "check": "NII arithmetic tie-out", "subject": f"{r['bank']} {r['quarter']}",
            "passed": bool(res.passed),
            "detail": (f"{r['interest_income_cr']:,.0f} − {r['interest_expended_cr']:,.0f} = "
                       f"{res.nii_computed:,.0f} vs printed {res.nii_reported:,.0f}"),
        })

    derived = df[df["nii_source"] == "derived"]["bank"].unique()
    no_split = df[(df["nii_source"] == "reported")
                  & df["interest_income_cr"].isna()]["bank"].unique()
    lines += [
        "",
        "*Not tie-outable — NII derived, no printed NII line to check against:* "
        f"{', '.join(sorted(derived)) or 'none'}.",
        "*Not tie-outable — NII printed but no interest income/expended split "
        f"disclosed:* {', '.join(sorted(no_split)) or 'none'}.",
        "",
    ]
    for b in sorted(derived):
        recs.append({"check": "NII arithmetic tie-out", "subject": b, "passed": None,
                     "detail": "NII derived — no printed NII line to check against"})
    for b in sorted(no_split):
        recs.append({"check": "NII arithmetic tie-out", "subject": b, "passed": None,
                     "detail": "NII printed but no interest income/expended split disclosed"})
    return lines, ok, recs


def check_stated_growth(df: pd.DataFrame, stated: pd.DataFrame) -> tuple[list[str], bool, list[dict]]:
    lines = [
        "## 2. Computed growth vs the bank's own published growth",
        "",
        "Recomputes YoY growth from the extracted absolute figures and compares "
        "it against the percentage the bank itself printed. A transcription "
        "error in either quarter breaks this check.",
        "",
    ]
    ok = True
    recs: list[dict] = []
    col = {"nii": "nii_cr", "pat": "pat_cr",
           "interest_income": "interest_income_cr",
           "interest_expended": "interest_expended_cr"}
    cur = df[df["quarter"] == Q_CURRENT].set_index("bank")
    pri = df[df["quarter"] == Q_PRIOR].set_index("bank")

    for _, s in stated.iterrows():
        c = col[s["metric"]]
        computed = growth(cur.loc[s["bank"], c], pri.loc[s["bank"], c])
        if computed is None:
            continue
        diff = abs(computed - s["stated_yoy_pct"])
        passed = diff <= s["tolerance_pp"]
        ok &= passed
        lines.append(
            f"- **{s['bank']} — {s['metric']}**: {'PASS' if passed else 'FAIL'} — "
            f"computed {computed:+.2f}% vs bank-stated {s['stated_yoy_pct']:+.1f}% "
            f"(diff {diff:.2f}pp, tolerance {s['tolerance_pp']}pp)"
        )
        recs.append({
            "check": "Computed vs published growth",
            "subject": f"{s['bank']} — {s['metric']}", "passed": bool(passed),
            "detail": (f"computed {computed:+.2f}% vs bank-stated {s['stated_yoy_pct']:+.1f}% "
                       f"(tolerance {s['tolerance_pp']}pp)"),
        })
    lines.append("")
    return lines, ok, recs


def check_pnl_walk(df: pd.DataFrame) -> tuple[list[str], bool, list[dict]]:
    """NII + other income - opex - provisions - tax == reported PAT.

    This is what licenses the attribution in build_bridge(): the five
    components have to actually sum to the bottom line before the change in
    the bottom line can be split across them.
    """
    lines = [
        "## 3. P&L walk to reported profit",
        "",
        "Net interest income + other income − operating expenses − provisions "
        "− tax must equal the bank's own reported profit after tax, for every "
        "bank in both quarters. This is the check the profit attribution rests "
        "on: if the components did not sum to the printed bottom line, "
        "decomposing the change in that bottom line across them would be "
        "meaningless.",
        "",
    ]
    ok = True
    recs: list[dict] = []
    for _, r in df.iterrows():
        walk = (r["nii_cr"] + r["other_income_cr"] - r["opex_cr"]
                - r["provisions_cr"] - r["tax_cr"])
        diff = walk - r["pat_cr"]
        tol = walk_tolerance(r["bank"])
        passed = abs(diff) <= tol
        ok &= passed
        lines.append(
            f"- **{r['bank']} {r['quarter']}**: {'PASS' if passed else 'FAIL'} — "
            f"{r['nii_cr']:,.2f} + {r['other_income_cr']:,.2f} − "
            f"{r['opex_cr']:,.2f} − {r['provisions_cr']:,.2f} − "
            f"{r['tax_cr']:,.2f} = {walk:,.2f} vs reported PAT "
            f"{r['pat_cr']:,.2f} (diff {diff:+,.2f}, tolerance ±{tol:,.2f} Cr)"
        )
        recs.append({
            "check": "P&L walk to reported PAT",
            "subject": f"{r['bank']} {r['quarter']}", "passed": bool(passed),
            "detail": (f"walk {walk:,.0f} vs reported PAT {r['pat_cr']:,.0f} "
                       f"(diff {diff:+,.0f}, tolerance ±{tol:,.0f} Cr)"),
        })
    lines += [
        "",
        "*Tolerances are derived from each bank's own reporting precision, not "
        "chosen. A figure printed to the nearest unit u carries up to u/2 of "
        "rounding, and this walk sums five of them, so the tolerance is 5·u/2. "
        "HDFC's is the widest because it publishes in ₹ billion to one decimal "
        "(u = ₹10 Cr); ICICI's is the tightest because it publishes ₹ Crore to "
        "two decimals (u = ₹0.01 Cr).*",
        "",
    ]
    return lines, ok, recs


def reconcile(df: pd.DataFrame, stated: pd.DataFrame) -> tuple[list[str], bool, list[dict]]:
    header = [
        "# Reconciliation Log — Bank Margin, Credit Cost & Profit Attribution",
        "",
        "Generated by `src/nim_bridge.py`. Four independent checks; all must "
        "pass before the bridge is written.",
        "",
    ]
    l1, ok1, r1 = check_nii_tieout(df)
    l2, ok2, r2 = check_stated_growth(df, stated)
    l3, ok3, r3 = check_pnl_walk(df)
    ok = ok1 and ok2 and ok3
    lines = header + l1 + l2 + l3 + [
        f"**Overall: {'all checks passed' if ok else 'CHECKS FAILED — see above'}**"
    ]
    RECON_LOG.parent.mkdir(parents=True, exist_ok=True)
    RECON_LOG.write_text("\n".join(lines) + "\n")
    return lines, ok, r1 + r2 + r3


def build_bridge(df: pd.DataFrame) -> pd.DataFrame:
    """Per-bank YoY comparison plus the profit attribution.

    Attribution convention: each component's contribution is its effect on
    profit, so a rise in NII or other income contributes positively while a
    rise in opex, provisions or tax contributes negatively.
    Check 3 is what makes the identity hold against the banks' own reported
    figures rather than only within this file.

    The five contributions sum to the change in PAT up to the rounding in the
    banks' published figures, which `rounding_residual_cr` records explicitly
    rather than absorbing into one of the components. It is zero for Axis,
    ICICI and Kotak and non-zero only for HDFC, whose income statement is
    printed in ₹ billion to one decimal. verify_attribution() bounds that
    residual by what the reporting precision can actually produce, so it
    cannot quietly soak up a genuine extraction error.

    Contributions are also expressed as a percentage of prior-year PAT, which
    is what makes them comparable across banks of very different size: HDFC's
    profit is roughly six times Kotak's, so rupee contributions alone say
    little about which lever mattered more to each bank.
    """
    cur = df[df["quarter"] == Q_CURRENT].set_index("bank")
    pri = df[df["quarter"] == Q_PRIOR].set_index("bank")

    rows = []
    for bank in cur.index:
        c, p = cur.loc[bank], pri.loc[bank]

        d_nii = c["nii_cr"] - p["nii_cr"]
        d_oi = c["other_income_cr"] - p["other_income_cr"]
        d_opex = -(c["opex_cr"] - p["opex_cr"])
        d_prov = -(c["provisions_cr"] - p["provisions_cr"])
        d_tax = -(c["tax_cr"] - p["tax_cr"])
        d_pat = c["pat_cr"] - p["pat_cr"]
        base = p["pat_cr"]

        rows.append({
            "bank": bank,
            # headline YoY
            "nii_growth_yoy_pct": growth(c["nii_cr"], p["nii_cr"]),
            "nii_source": c["nii_source"],
            "pat_growth_yoy_pct": growth(c["pat_cr"], p["pat_cr"]),
            "other_income_growth_yoy_pct": growth(c["other_income_cr"], p["other_income_cr"]),
            "opex_growth_yoy_pct": growth(c["opex_cr"], p["opex_cr"]),
            "provisions_change_yoy_pct": growth(c["provisions_cr"], p["provisions_cr"]),
            "advances_growth_yoy_pct": growth(c["advances_cr"], p["advances_cr"]),
            "advances_basis": c["advances_basis"],
            # ratio changes
            "nim_change_bps": delta_bps(c["nim_pct"], p["nim_pct"]),
            "gnpa_change_bps": delta_bps(c["gnpa_pct"], p["gnpa_pct"]),
            "credit_cost_change_bps": delta_bps(c["credit_cost_pct"], p["credit_cost_pct"]),
            "credit_cost_definition": c["credit_cost_definition"],
            # profit attribution, Rs Crore
            "delta_pat_cr": d_pat,
            "contrib_nii_cr": d_nii,
            "contrib_other_income_cr": d_oi,
            "contrib_opex_cr": d_opex,
            "contrib_provisions_cr": d_prov,
            "contrib_tax_cr": d_tax,
            "rounding_residual_cr": d_pat - (d_nii + d_oi + d_opex + d_prov + d_tax),
            # profit attribution, % of prior-year PAT
            "contrib_nii_pct_of_prior_pat": d_nii / base * 100,
            "contrib_other_income_pct_of_prior_pat": d_oi / base * 100,
            "contrib_opex_pct_of_prior_pat": d_opex / base * 100,
            "contrib_provisions_pct_of_prior_pat": d_prov / base * 100,
            "contrib_tax_pct_of_prior_pat": d_tax / base * 100,
            # levels, both quarters
            "nim_q1fy26_pct": p["nim_pct"], "nim_q1fy27_pct": c["nim_pct"],
            "gnpa_q1fy26_pct": p["gnpa_pct"], "gnpa_q1fy27_pct": c["gnpa_pct"],
            "credit_cost_q1fy26_pct": p["credit_cost_pct"],
            "credit_cost_q1fy27_pct": c["credit_cost_pct"],
            "nii_q1fy26_cr": p["nii_cr"], "nii_q1fy27_cr": c["nii_cr"],
            "pat_q1fy26_cr": p["pat_cr"], "pat_q1fy27_cr": c["pat_cr"],
            "provisions_q1fy26_cr": p["provisions_cr"],
            "provisions_q1fy27_cr": c["provisions_cr"],
        })
    return pd.DataFrame(rows).sort_values("pat_growth_yoy_pct", ascending=False)


def verify_attribution(bridge: pd.DataFrame) -> tuple[list[str], bool, list[dict]]:
    """The five contributions must sum back to the change in PAT, within the
    rounding the banks' own published figures can produce.

    The change in PAT is a difference of two quarters, each of which is a
    five-line walk, so the bound is twice the walk tolerance. Anything larger
    is an extraction error, not rounding, and fails.
    """
    lines = [
        "## 4. Attribution closes on the change in profit",
        "",
        "The five contributions must sum back to the YoY change in reported "
        "profit. The residual is bounded by twice the walk tolerance, because "
        "the change is a difference of two quarters that are each a five-line "
        "walk. A residual larger than the banks' own rounding can produce is "
        "an extraction error, not rounding, and fails here.",
        "",
    ]
    ok = True
    recs: list[dict] = []
    for _, r in bridge.iterrows():
        resid = r["rounding_residual_cr"]
        bound = 2 * walk_tolerance(r["bank"])
        passed = abs(resid) <= bound
        ok &= passed
        lines.append(
            f"- **{r['bank']}**: {'PASS' if passed else 'FAIL'} — contributions "
            f"sum to {r['delta_pat_cr'] - resid:+,.2f} vs reported ΔPAT "
            f"{r['delta_pat_cr']:+,.2f} (residual {resid:+,.2f} Cr, "
            f"bound ±{bound:,.2f} Cr)"
        )
        recs.append({
            "check": "Attribution closes on ΔPAT", "subject": r["bank"],
            "passed": bool(passed),
            "detail": (f"residual {resid:+,.0f} Cr against ΔPAT "
                       f"{r['delta_pat_cr']:+,.0f} Cr (bound ±{bound:,.0f} Cr)"),
        })
    lines.append("")
    return lines, ok, recs


if __name__ == "__main__":
    df = pd.read_csv(INPUT_CSV)
    stated = pd.read_csv(STATED_CSV)

    log, ok, _ = reconcile(df, stated)
    print("\n".join(log))
    if not ok:
        sys.exit("Reconciliation failed — refusing to write the bridge.")

    bridge = build_bridge(df)
    l4, ok4, _ = verify_attribution(bridge)
    print()
    print("\n".join(l4))
    # Check 4 needs the built bridge, so the log is rewritten with it appended.
    RECON_LOG.write_text(
        "\n".join(log[:-1] + l4 + [
            f"**Overall: {'all checks passed' if ok and ok4 else 'CHECKS FAILED — see above'}**"
        ]) + "\n"
    )
    if not ok4:
        sys.exit("Attribution does not close on the change in PAT — refusing to write.")

    print()
    print("YoY comparison")
    print(bridge[["bank", "nii_growth_yoy_pct", "pat_growth_yoy_pct",
                  "provisions_change_yoy_pct", "nim_change_bps",
                  "gnpa_change_bps", "credit_cost_change_bps"]]
          .to_string(index=False))
    print()
    print("Profit attribution (% of prior-year PAT)")
    print(bridge[["bank", "contrib_nii_pct_of_prior_pat",
                  "contrib_other_income_pct_of_prior_pat",
                  "contrib_opex_pct_of_prior_pat",
                  "contrib_provisions_pct_of_prior_pat",
                  "contrib_tax_pct_of_prior_pat", "pat_growth_yoy_pct"]]
          .to_string(index=False))

    bridge.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWritten: {OUTPUT_CSV}")
