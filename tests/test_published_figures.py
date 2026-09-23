"""Guards the defect class that actually bit this project: published figures
drifting away from the data after the inputs were corrected.

Charts, memos and READMEs are generated or written at different times. When a
source figure changes, anything already written keeps the old number and still
looks authoritative. These tests re-read the CSVs and assert that every figure
quoted in the README, embedded in the dashboard, or printed in the memo still
matches. They fail on stale prose, which is exactly what is wanted.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = pd.read_csv(ROOT / "data" / "final" / "margin_bridge.csv").set_index("bank")
INPUTS = pd.read_csv(ROOT / "data" / "final" / "verified_inputs.csv")
README = (ROOT / "README.md").read_text()

SHORT = {"Kotak Mahindra Bank": "Kotak Mahindra Bank", "Axis Bank": "Axis Bank",
         "ICICI Bank": "ICICI Bank", "HDFC Bank": "HDFC Bank"}


def _readme_row(bank: str) -> list[str]:
    for line in README.splitlines():
        if line.strip().startswith(f"| {bank} |"):
            return [c.strip().strip("*") for c in line.strip().strip("|").split("|")]
    raise AssertionError(f"no README table row found for {bank}")


@pytest.mark.parametrize("bank", list(SHORT))
def test_readme_attribution_row_matches_bridge(bank):
    """The README's attribution table is hand-written; the CSV is generated."""
    cells = _readme_row(bank)
    cols = ["contrib_nii_pct_of_prior_pat", "contrib_other_income_pct_of_prior_pat",
            "contrib_opex_pct_of_prior_pat", "contrib_provisions_pct_of_prior_pat",
            "contrib_tax_pct_of_prior_pat"]
    for cell, col in zip(cells[1:6], cols):
        got = float(cell.replace("−", "-").replace("+", ""))
        assert got == pytest.approx(BRIDGE.loc[bank, col], abs=0.05), (
            f"README {bank} {col}: says {got}, data says {BRIDGE.loc[bank, col]:.1f}")
    pat = float(cells[6].replace("−", "-").replace("+", "").rstrip("%"))
    assert pat == pytest.approx(BRIDGE.loc[bank, "pat_growth_yoy_pct"], abs=0.05)


def test_readme_quotes_no_stale_icici_growth():
    """An earlier revision published +13.9% / +12.3% for ICICI, from the
    consolidated basis. Those must not reappear anywhere in the README."""
    for stale in ("+13.9%", "+12.3%"):
        assert stale not in README, f"stale pre-correction ICICI figure {stale} is back in README"


def test_dashboard_matches_bridge():
    html = (ROOT / "outputs" / "dashboard" / "index.html").read_text()
    data = json.loads(re.search(r"const DATA = (\{.*?\});\n", html, re.S).group(1))
    assert data["banks"], "dashboard embedded no banks"
    for b in data["banks"]:
        row = BRIDGE.loc[b["bank"]]
        assert b["patGrowth"] == pytest.approx(row["pat_growth_yoy_pct"])
        for k in ("nii", "other_income", "opex", "provisions", "tax"):
            assert b["contrib"][k] == pytest.approx(row[f"contrib_{k}_pct_of_prior_pat"])


def test_dashboard_waterfalls_close_on_reported_pat():
    html = (ROOT / "outputs" / "dashboard" / "index.html").read_text()
    data = json.loads(re.search(r"const DATA = (\{.*?\});\n", html, re.S).group(1))
    for b in data["banks"]:
        walk = b["patPrior"] + sum(b["contribCr"].values()) + b["residualCr"]
        assert walk == pytest.approx(b["patCurrent"], abs=1e-6), (
            f"{b['bank']}: the waterfall drawn on the dashboard does not reach reported PAT")


def test_dashboard_embeds_no_failing_check():
    html = (ROOT / "outputs" / "dashboard" / "index.html").read_text()
    data = json.loads(re.search(r"const DATA = (\{.*?\});\n", html, re.S).group(1))
    failed = [c for c in data["checks"] if c["passed"] is False]
    assert not failed, f"dashboard published with failing checks: {failed}"


def test_every_input_row_carries_a_source_citation():
    missing = INPUTS[INPUTS["source_page_note"].isna()
                     | (INPUTS["source_page_note"].astype(str).str.strip() == "")]
    assert missing.empty, f"rows without a page citation:\n{missing[['bank', 'quarter']]}"


def test_gnpa_is_gross_not_net():
    """Net NPA was once recorded in the gross column. Gross must exceed net."""
    rows = INPUTS.dropna(subset=["gnpa_pct", "net_npa_pct"])
    assert not rows.empty
    bad = rows[rows["gnpa_pct"] <= rows["net_npa_pct"]]
    assert bad.empty, f"gross NPA not above net NPA — columns may be swapped:\n{bad}"


@pytest.mark.skipif(not (ROOT / "reports" / "methodology_memo.pdf").exists(),
                    reason="memo not built")
def test_memo_quotes_current_pat_growth():
    try:
        text = subprocess.run(
            ["pdftotext", str(ROOT / "reports" / "methodology_memo.pdf"), "-"],
            capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("pdftotext unavailable")
    for bank in SHORT:
        want = f"{BRIDGE.loc[bank, 'pat_growth_yoy_pct']:+.1f}%".replace("+", "")
        assert want in text, f"memo does not quote {bank}'s current PAT growth of {want}"
