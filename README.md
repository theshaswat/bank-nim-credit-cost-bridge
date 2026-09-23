# Bank Margin & Credit-Cost Bridge

Four private-sector banks — HDFC Bank, ICICI Bank, Axis Bank, Kotak Mahindra
Bank — compared Q1 FY27 against Q1 FY26 (quarters ended 30 June) on what
actually moved profit: net interest income, other income, operating costs,
provisions and tax. Built from each bank's own results filings, all on a
standalone basis, with every figure page-cited and four reconciliation checks
that have to pass before any comparison is written.

Full writeup: [`reports/methodology_memo.pdf`](reports/methodology_memo.pdf).

Complements [`bank-lcr-funding-concentration`](https://github.com/theshaswat/bank-lcr-funding-concentration),
which covers liquidity and LCR for a different bank set. This one is about
margin and profit, and does not overlap it.

## The question

All four banks grew profit in Q1 FY27. That single number hides the fact that
the four got there in very different ways. The question here is how much of
each bank's profit growth came from the lending business widening, and how
much came from provisioning less against it — because only one of those is
repeatable.

## Findings

The margin narrowed at all three banks that publish one — ICICI does not —
and profit grew at all four. The line that reconciles those two facts is
provisions.

**Where the profit growth came from** — each component's contribution in
percentage points of the prior-year quarter's profit. They sum to reported
PAT growth, which is the last column:

| Bank | Net interest income | Other income | Operating expenses | Provisions | Tax | **Reported PAT growth** |
|---|---:|---:|---:|---:|---:|---:|
| Kotak Mahindra Bank | +20.4 | +7.9 | −11.0 | **+16.5** | −8.1 | **+25.6%** |
| Axis Bank | +18.7 | −9.0 | −7.2 | **+29.7** | −9.7 | **+22.5%** |
| ICICI Bank | +21.5 | +0.6 | −9.2 | **+4.3** | −1.2 | **+15.9%** |
| HDFC Bank | +11.5 | −49.1 | −4.2 | **+62.7** | −16.1 | **+5.0%** |

Read the provisions column against the last one. Axis grew profit 22.5%, and
the fall in provisions alone contributed 29.7 points of that — more than the
entire increase. Strip provisions and tax out and the operating business
contributed 2.5 points. ICICI is the opposite case: 12.8 of its 15.9 points
came from operations, and only 3.1 from the provision and tax lines. On the
evidence in these four filings, ICICI's profit growth is the least dependent
on the credit cycle staying benign, and Axis's is the most.

HDFC's +5.0% is the number most likely to be misread. Its other income fell
41% YoY, which costs 49 points — but that is a base effect, not deterioration:
the June 2025 quarter contained a one-time gain on the partial divestment of
HDB Financial Services. Against that ₹8,910 Cr fall in other income sits a
₹11,380 Cr fall in provisions, which more than covers it. Neither side is a
run-rate, and the +5.0% headline is the residue of two large one-offs pulling
in opposite directions rather than a reading on the underlying business.

**Margins and asset quality:**

| Bank | NII growth | NIM change | Gross NPA change | Credit cost change |
|---|---:|---:|---:|---:|
| Kotak Mahindra Bank | +9.2% | −12 bps | −30 bps | −47 bps |
| Axis Bank | +8.0% | −34 bps | −29 bps | −75 bps |
| ICICI Bank | +12.7% | not disclosed | −33 bps | not disclosed |
| HDFC Bank | +6.6% | −9 bps | −23 bps | −16 bps |

Note that net interest income still grew everywhere despite margins narrowing
everywhere — the books grew faster than the margin compressed. And the gross
NPA ratio fell at all four banks, which is what distinguishes "provisions fell
because the book improved" from "provisions fell because the bank chose to
provide less." The first reading is the better supported one here, though a
single year-on-year comparison cannot settle it on its own.

## What the numbers will not support

Credit-cost **levels** are not comparable across these four banks. Each
defines the ratio differently — HDFC reports it gross of recoveries, Axis
reports net credit cost annualised, Kotak reports it on specific provisions
only. The year-on-year change within a bank is comparable; the level across
banks is not, and no chart here puts those levels side by side.

ICICI publishes neither a net interest margin nor a credit-cost ratio in this
filing, so those two cells are genuinely empty rather than omitted for
convenience. Its NII is **derived** here as interest earned less interest
expended, because ICICI prints no NII line — that is flagged in the data as
`nii_source = derived` and excluded from the arithmetic tie-out, since
checking a derived figure against its own definition would pass by
construction and prove nothing. The Q1 FY26 derivation does get an external
check: ICICI's Q1 FY26 investor presentation prints standalone NII of
₹216.35 bn, against ₹21,634.46 Cr derived here — ₹0.54 Cr apart. No
equivalent document was obtained for Q1 FY27.

Advances are on different bases: HDFC publishes average advances under
management, Kotak publishes period-end net advances. Both are recorded with
an explicit `advances_basis` column rather than being silently pooled.

## How the figures are checked

Four checks run in `src/nim_bridge.py`, and the bridge is not written unless
all four pass. Each is capable of failing on a transcription error — none of
them passes by construction:

1. **NII arithmetic tie-out.** Interest earned − interest expended = printed
   NII. Only runs for banks that publish both the split and their own NII
   line, which is Axis alone.
2. **Computed growth vs the bank's own published growth.** Recomputes YoY
   growth from the extracted absolutes and compares it against the percentage
   the bank itself printed, across eight bank-metric pairs. An error in either
   quarter breaks it.
3. **P&L walk.** NII + other income − opex − provisions − tax = reported PAT,
   for all four banks in both quarters. Tolerances are derived from each
   bank's own reporting precision, not chosen.
4. **Attribution closes.** The five contributions sum back to the reported
   change in profit, within the same bounded rounding.

Results: [`data/processed/reconciliation_log.md`](data/processed/reconciliation_log.md).

## Glossary

| Term | Meaning as used here |
|---|---|
| NII | Net interest income — interest earned less interest expended |
| NIM | Net interest margin, as each bank reports it on its own asset base |
| GNPA | Gross non-performing assets as a % of gross advances. Gross throughout — never net NPA, which is reported separately in `net_npa_pct` |
| Credit cost | Provisions as an annualised % of advances, on each bank's own definition |
| bps | Basis points; 100 bps = 1 percentage point |
| Standalone | The bank alone, excluding subsidiaries — used for all four banks so they are comparable |
| Q1 FY27 | Quarter ended 30 June 2026. Q1 FY26 is the quarter ended 30 June 2025 |

## Project structure

```
bank-nim-credit-cost-bridge/
├── data/
│   ├── raw/
│   │   ├── investor_decks/       # 7 real, unmodified source PDFs
│   │   ├── bank_stated_yoy.csv   # growth % as each bank printed it (check 2)
│   │   └── source_manifest.md    # URL, retrieval date, SHA-256 per file
│   ├── processed/
│   │   └── reconciliation_log.md # all four checks, per bank, per quarter
│   └── final/
│       ├── verified_inputs.csv   # hand-extracted, page-cited figures
│       └── margin_bridge.csv     # computed comparatives + attribution
├── src/
│   ├── nim_bridge.py             # reconciliation + attribution
│   ├── build_charts.py           # the 3 exhibits in outputs/charts/
│   ├── build_pdf.py              # the methodology memo
│   └── build_dashboard.py        # the interactive dashboard
├── outputs/
│   ├── charts/                   # 3 PNG exhibits, one question each
│   └── dashboard/index.html      # self-contained, no external requests
├── reports/
│   └── methodology_memo.pdf      # full writeup — read this first
├── tests/
│   └── test_published_figures.py # asserts docs/dashboard match the data
├── requirements.txt
├── DATA_DICTIONARY.md
├── LIMITATIONS.md
├── LICENSE
└── README.md
```

## How to run

```bash
pip install -r requirements.txt
python src/nim_bridge.py     # runs the 4 checks, writes margin_bridge.csv
python src/build_charts.py   # writes outputs/charts/*.png
python src/build_pdf.py      # writes reports/methodology_memo.pdf
python src/build_dashboard.py # writes outputs/dashboard/index.html
pytest tests                 # asserts the published figures match the data
```

`outputs/dashboard/index.html` opens straight from disk — one file, no external
requests, no build step. Every figure in it is generated from `data/final/`
and the four checks are re-run when it is built, so the page cannot be
published showing a figure the data does not support.

`requirements.txt` installs [`indfin`](https://github.com/theshaswat/indfin),
the shared reconciliation library this project and
[`epc-earnings-quality-screen`](https://github.com/theshaswat/epc-earnings-quality-screen)
both build on. No sibling checkout or path manipulation is needed.

## Data and sources

Q1 FY26 and Q1 FY27 investor presentations and results filings, downloaded
from each bank's investor-relations page. URLs, retrieval timestamps and
SHA-256 hashes for every file: [`data/raw/source_manifest.md`](data/raw/source_manifest.md).

One gap worth stating up front: Kotak's Q1 FY26 deck downloaded with a
corrupted internal structure and was dropped rather than special-cased into
the pipeline. Both Kotak quarters come from the Q1 FY27 deck's own
comparative columns instead.

## Limitations

See [`LIMITATIONS.md`](LIMITATIONS.md). The short version: four banks, two
quarters, one year-on-year comparison. It is a reconciliation and attribution
exercise, not a panel regression, and it cannot separate a genuine credit-cycle
improvement from the tail of a provisioning cycle on one year of data.

## Author

Shaswat Sharma — [github.com/theshaswat](https://github.com/theshaswat)
