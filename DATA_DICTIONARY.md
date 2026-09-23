# Data Dictionary

All monetary columns are in **₹ Crore** and carry a `_cr` suffix. All ratio
columns are in **percent** and carry a `_pct` suffix. Changes in ratios are in
**basis points** and carry a `_bps` suffix. Nothing in this repository mixes
units within a column — the earlier revision of this project did, and that is
the specific mistake the suffix convention exists to prevent.

## `data/final/verified_inputs.csv`

One row per bank per quarter. Eight rows: four banks × two quarters.

| Column | Type | Description |
|---|---|---|
| `bank` | string | Bank name as it appears in its own filing |
| `basis` | string | `standalone` for all eight rows — see the basis note below |
| `quarter` | string | `Q1 FY26` or `Q1 FY27` (quarters ended 30 June 2025 and 30 June 2026) |
| `interest_income_cr` | float, ₹ Cr | Interest earned. Populated only where the bank prints the split (Axis, ICICI) |
| `interest_expended_cr` | float, ₹ Cr | Interest expended. Same availability |
| `nii_cr` | float, ₹ Cr | Net interest income, all four banks |
| `nii_source` | string | `reported` if the bank prints an NII line; `derived` if computed here as interest earned less interest expended. Only ICICI is `derived` |
| `other_income_cr` | float, ₹ Cr | Non-interest / other income |
| `opex_cr` | float, ₹ Cr | Operating expenses |
| `provisions_cr` | float, ₹ Cr | Provisions and contingencies, excluding tax |
| `tax_cr` | float, ₹ Cr | Provision for tax. For HDFC, which prints no tax line, this is PBT less PAT |
| `pat_cr` | float, ₹ Cr | Profit after tax as the bank reports it |
| `advances_cr` | float, ₹ Cr | Advances. Populated for HDFC and Kotak; see `advances_basis` |
| `advances_basis` | string | What `advances_cr` actually measures — `average advances under management` (HDFC) or `period-end net advances` (Kotak). These are different measures and are not pooled |
| `deposits_cr` | float, ₹ Cr | Deposits, on the same basis as that bank's advances |
| `nim_pct` | float, % | Reported net interest margin. Not disclosed by ICICI |
| `gnpa_pct` | float, % | **Gross** NPA ratio, all four banks. Never net NPA |
| `net_npa_pct` | float, % | Net NPA ratio, kept in its own column so it can never be confused with the gross figure |
| `credit_cost_pct` | float, % | Reported credit-cost ratio. Not disclosed by ICICI |
| `credit_cost_definition` | string | How that bank defines the ratio. **Levels are not comparable across banks** because these differ; see below |
| `source_page_note` | string | The exact filing and page each figure on this row came from |

**Basis note.** All four banks are on a **standalone** basis. ICICI's
consolidated results include large insurance subsidiaries and are not
comparable with the other three banks' standalone figures; its standalone
results appear in the same filing and are what this project uses.

**Credit-cost definitions differ.** HDFC reports credit cost gross of
recoveries; Axis reports net credit cost annualised; Kotak reports it on
specific provisions only. The year-on-year change within a bank is a fair
comparison. The level between banks is not, and no exhibit in this repository
places those levels side by side.

**Blank cells are genuine non-disclosure.** No cell is filled from a secondary
source. Where a bank does not publish a figure in its own filing for the
quarter, the cell stays empty and the reason is recorded in
[`LIMITATIONS.md`](LIMITATIONS.md).

## `data/raw/bank_stated_yoy.csv`

The growth percentages each bank printed itself, used by reconciliation
check 2. Keeping these separate from the extracted absolutes is what makes
that check independent.

| Column | Type | Description |
|---|---|---|
| `bank` | string | Bank name |
| `metric` | string | `nii`, `pat`, `interest_income` or `interest_expended` |
| `stated_yoy_pct` | float, % | The growth figure as the bank printed it |
| `tolerance_pp` | float, pp | Allowed gap, set by how precisely that bank prints the figure |
| `source_page_note` | string | Filing and page |

## `data/final/margin_bridge.csv`

Output of `src/nim_bridge.py::build_bridge()`. One row per bank.

**Growth and change columns**

| Column | Description |
|---|---|
| `nii_growth_yoy_pct`, `pat_growth_yoy_pct`, `other_income_growth_yoy_pct`, `opex_growth_yoy_pct`, `provisions_change_yoy_pct`, `advances_growth_yoy_pct` | `(Q1FY27 / Q1FY26 − 1) × 100` |
| `nim_change_bps`, `gnpa_change_bps`, `credit_cost_change_bps` | `(Q1FY27 − Q1FY26) × 100`, in basis points |
| `nii_source`, `advances_basis`, `credit_cost_definition` | Carried through from the inputs so no figure is read without its caveat |

**Profit attribution.** Each component's effect on profit: a rise in NII or
other income contributes positively, a rise in opex, provisions or tax
contributes negatively.

| Column | Description |
|---|---|
| `delta_pat_cr` | Change in reported PAT, ₹ Cr |
| `contrib_nii_cr`, `contrib_other_income_cr`, `contrib_opex_cr`, `contrib_provisions_cr`, `contrib_tax_cr` | Each component's contribution, ₹ Cr |
| `contrib_*_pct_of_prior_pat` | The same five, as a percentage of the prior-year quarter's PAT. This is what makes banks of different size comparable — HDFC's profit is roughly six times Kotak's |
| `rounding_residual_cr` | `delta_pat_cr` less the sum of the five contributions. Zero for Axis, ICICI and Kotak; −₹20 Cr for HDFC, which prints its income statement in ₹ billion to one decimal. Recorded explicitly rather than absorbed into a component, and bounded by check 4 |

**Level columns.** `nim_q1fy26_pct` / `nim_q1fy27_pct`, and the same pairs for
`gnpa`, `credit_cost`, `nii_cr`, `pat_cr` and `provisions_cr` — the raw figures
behind every growth number, so any percentage in this file can be recomputed
without opening the inputs.

## `data/processed/reconciliation_log.md`

Auto-generated by `src/nim_bridge.py`. Records all four checks, per bank and
per quarter, with the actual arithmetic shown. The bridge is not written
unless every check passes. See the "How the figures are checked" section of
[`README.md`](README.md) for what each check does and why check 1 deliberately
skips ICICI.

## `data/raw/source_manifest.md`

One entry per source PDF: bank, period, download URL, retrieval timestamp and
SHA-256 hash, plus notes on each filing's layout and any extraction caveat.
