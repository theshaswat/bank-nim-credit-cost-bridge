# Bank Margin & Profitability Bridge

Four private-sector banks — HDFC Bank, Axis Bank, ICICI Bank, Kotak Mahindra
Bank — compared Q1 FY26 vs Q1 FY27 (quarter ended 30-Jun, YoY) on what
actually moved profit: net interest income growth, margin, asset quality,
and credit cost. Built entirely from each bank's own investor decks and
results filings, using only the metrics each bank actually discloses.

Full writeup: [`reports/methodology_memo.pdf`](reports/methodology_memo.pdf).

Complements [`bank-lcr-funding-concentration`](https://github.com/theshaswat/bank-lcr-funding-concentration)
(HDFC + IndusInd liquidity/LCR only) — this project covers margin and
profitability, not liquidity, across a different and non-overlapping bank
set.

## The question

Four banks reported Q1 FY27 profit growth. This asks what's underneath that
one number for each — did profit grow because the core lending business
widened, because credit costs fell, or some mix — using each bank's own
disclosures rather than a model that assumes every bank discloses the same
thing.

## Findings

| Bank | PAT Growth YoY | NII Growth YoY | NIM Δ | GNPA% Δ | Credit Cost Δ |
|---|---|---|---|---|---|
| Kotak Mahindra Bank | +25.6% | — | −12 bps | −7 bps | −47 bps |
| Axis Bank | +22.5% | +8.0% | — | — | — |
| ICICI Bank | +13.9% | +12.3% | — | — | — |
| HDFC Bank | +4.9% | — | −9 bps | −23 bps | — |

Blank cells are not zeros — they mean that bank doesn't disclose that figure
in a form this project could independently verify. Nothing here is
estimated or filled in to complete a row.

## Why this isn't a 12-quarter rate/volume/mix panel

The original scope was a three-factor rate/volume/mix decomposition of NII
across a full quarterly panel. It didn't survive contact with the actual
disclosures: Axis and ICICI publish a clean Interest Income / Interest
Expended / NII table, while HDFC and Kotak publish average balances and a
headline NIM% directly — their yield/cost-of-funds figures exist only as
chart labels that don't map unambiguously to values through plain-text PDF
extraction. Forcing one model across all four would have meant guessing at
two of the four banks' numbers. See [`LIMITATIONS.md`](LIMITATIONS.md) and
the memo's Method section for the full reasoning.

## Project structure

```
bank-nim-credit-cost-bridge/
├── data/
│   ├── raw/
│   │   ├── investor_decks/       # 7 real, unmodified source PDFs
│   │   └── source_manifest.md    # URL, retrieval date, SHA-256 per file
│   ├── processed/
│   │   └── reconciliation_log.md # NII tie-out results (Axis, ICICI)
│   └── final/
│       ├── verified_inputs.csv   # hand-extracted, page-cited figures
│       └── margin_bridge.csv     # computed YoY comparatives
├── src/
│   ├── nim_bridge.py             # reconciliation + comparative computation
│   ├── build_charts.py           # the 3 exhibits in outputs/charts/
│   └── build_pdf.py              # the methodology memo
├── outputs/
│   └── charts/                   # 3 PNG exhibits, no overlap in content
├── reports/
│   └── methodology_memo.pdf      # full writeup — read this first
├── requirements.txt
├── DATA_DICTIONARY.md
├── LIMITATIONS.md
├── LICENSE
└── README.md
```

## How to run

```bash
# from the parent directory containing both this repo and indfin/
pip install -r bank-nim-credit-cost-bridge/requirements.txt
cd bank-nim-credit-cost-bridge
python src/nim_bridge.py     # reconciles NII, computes margin_bridge.csv
python src/build_charts.py   # writes outputs/charts/*.png
python src/build_pdf.py      # writes reports/methodology_memo.pdf
```

Requires [`indfin`](https://github.com/theshaswat/indfin) cloned as a sibling
directory (`../indfin`) — the shared reconciliation/extraction library this
project and [`epc-earnings-quality-screen`](https://github.com/theshaswat/epc-earnings-quality-screen)
both depend on.

## Data / sources

Bank Q1 FY26 and Q1 FY27 investor presentations / results filings,
downloaded directly from each bank's investor-relations page. Full URLs,
retrieval timestamps, and SHA-256 hashes for every source file:
`data/raw/source_manifest.md`. One gap worth noting up front: Kotak's
Q1FY26 deck downloaded with a corrupted internal file structure and was
dropped rather than special-cased into the pipeline — both Kotak quarters
in this project come from the Q1FY27 deck's own comparative columns
instead. See `data/raw/source_manifest.md` for the full account.

## Limitations

See [`LIMITATIONS.md`](LIMITATIONS.md) — most importantly, this is a
4-bank, 2-quarter comparative bridge, not a panel regression, and it
deliberately doesn't attempt the full rate/volume/mix decomposition or any
wild-cluster bootstrap inference.

## Author

Shaswat Sharma — [github.com/theshaswat](https://github.com/theshaswat)
