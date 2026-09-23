# Source Manifest — Bank NIM & Credit-Cost Bridge

Every file in `data/raw/` is logged here on download: exact URL, retrieval
timestamp, and a SHA-256 hash.

| File | Bank | Period | URL | Retrieved | SHA-256 |
|---|---|---|---|---|---|
| investor_decks/HDFCBANK_Q1FY27_deck.pdf | HDFC Bank | Q1 FY27 (qtr ended 30-Jun-2026) | https://www.hdfc.bank.in/content/dam/hdfcbankpws/in/en/pdf/about-us/financial-results/2026-2027/quarter-1/q1fy27-earnings-presentation.pdf | 2026-09-23T00:49 IST | `5bece3e8d330c0f75ee4ab36d82a5af90b456d389fa881c30a6573d4fbc91e5e` |
| investor_decks/HDFCBANK_Q1FY26_deck.pdf | HDFC Bank | Q1 FY26 (qtr ended 30-Jun-2025) | https://www.hdfc.bank.in/content/dam/hdfcbankpws/in/en/pdf/about-us/financial-results/2025-2026/quarter-1/q1fy26-earnings-presentation.pdf | 2026-09-23T01:08 IST | `e08b2fb063898755a936be5e92d7c63ae0a9ab7daf9d0f9da525c93280089c52` |
| investor_decks/AXISBANK_Q1FY27_deck.pdf | Axis Bank | Q1 FY27 (qtr ended 30-Jun-2026) | https://www.axis.bank.in/docs/default-source/shareholders/financial-results-and-other-information/investor-presentations/2026-2027/investor-presentation-for-the-quarter-ended-30th-june-2026.pdf | 2026-09-23T01:08 IST | `257a7f3463ca346d5db3ad5f6269d1ebb0445a07858e1670e95e515f1c5d8cf5` |
| investor_decks/AXISBANK_Q1FY26_deck.pdf | Axis Bank | Q1 FY26 (qtr ended 30-Jun-2025) | https://www.axis.bank.in/docs/default-source/shareholders/financial-results-and-other-information/investor-presentations/2025---2026/investor-presentation-for-the-quarter-ended-30th-june-2025.pdf | 2026-09-23T01:08 IST | `919da1c6b41385fb270bdc1aeccf5c9e1f4c0bfbfd79a97b17059b0845913564` |
| investor_decks/ICICI_Q1FY26_deck.pdf | ICICI Bank | Q1 FY26 (qtr ended 30-Jun-2025) | https://www.icici.bank.in/content/dam/icicibank/india/managed-assets/docs/about-us/2026/2025-07-q1-2026-investor-presentation.pdf | 2026-09-23T01:08 IST | `1508d25436644bd39ecddc69961417a80c3e04bef3fcb04a9ccd8659229796ae` |
| investor_decks/ICICI_Q1FY27_deck.pdf | ICICI Bank | Q1 FY27 (qtr ended 30-Jun-2026) | https://www.icici.bank.in/content/dam/icicibank/india/managed-assets/docs/about-us/2027/financial-results-q1-2027.pdf | 2026-09-23T01:08 IST | `b95bef731a963323ad256416cf2cc473c3c2554f6c09e4a83744ee1a6a094e2a` |
| investor_decks/KOTAKBANK_Q1FY27_deck.pdf | Kotak Mahindra Bank | Q1 FY27 (qtr ended 30-Jun-2026), contains Q1 FY26 comparatives | https://www.kotak.bank.in/content/dam/Kotak/investor-relation/Financial-Result/QuarterlyReport/FY-2027/q1/Investor-Presentation/Q1FY27-Investor-Presentation.pdf | 2026-09-23T01:08 IST | `31f8caa16841747e4baae6d3312044459eca5711cfccdb91098d9b6caec288ee` |

All seven hashes re-verified against the files in `investor_decks/` at
build time (`shasum -a 256`) — match, no drift since download.

`bank_stated_yoy.csv` sits alongside them in `data/raw/`. It is not a
downloaded file: it records the year-on-year growth percentages each bank
printed in its own deck, transcribed with a page citation per row. It is
kept in `raw/` and separate from the extracted absolutes on purpose —
reconciliation check 2 compares growth recomputed from those absolutes
against these published figures, and that check is only independent if the
two sets of numbers never touch.

## Notes on the filings

- **HDFC Bank**: page 3 of each deck discloses average deposits and average
  advances under management directly, standalone basis, alongside the
  reported NIM%. Page 18 of the Q1FY27 deck carries a full GNPA bridge for
  two consecutive quarters on one page (`GNPA open → Slippages → Upgrades &
  Recoveries → Write-offs → GNPA close`, ₹ bn) — genuinely disclosed, not
  reconstructed. The yield-on-assets/cost-of-funds chart on page 14 presents
  its numbers with no unambiguous label-to-value mapping via plain-text PDF
  extraction; rather than guess at it, this project does not claim precise
  figures from that chart (see `LIMITATIONS.md`).
- **Axis Bank**: page 62 of the Q1FY27 deck carries a "Financial Performance"
  table with both Q1FY26 and Q1FY27 columns — Interest Income, Interest
  Expended, NII, and PAT all as clean line items. `indfin.reconcile.nii`
  ties Interest Income − Interest Expended to reported NII for both
  quarters (see `data/processed/reconciliation_log.md`) — exact match.
- **ICICI Bank**: both quarters come from **one** file — page 1 of the
  13-page Q1FY27 regulatory results filing, whose STANDALONE FINANCIAL
  RESULTS table carries Q1-2027 and Q1-2026 columns side by side for
  Interest earned, Other income, Interest expended, Operating expenses,
  Provisions, Tax and Net profit. That filing prints no net interest
  income line, so ICICI's NII is **derived** here as interest earned less
  interest expended, flagged `nii_source = derived`, and deliberately
  **excluded** from the `check_nii` tie-out, because checking a derived
  figure against the definition it came from would pass by construction.
  `ICICI_Q1FY26_deck.pdf` is retained for one reason: its page 7 profit &
  loss statement does print standalone NII, at ₹216.35 bn for Q1-2026,
  against ₹21,634.46 Cr derived here — ₹0.54 Cr apart, which corroborates
  the derivation from outside its own definition. No Q1FY27 document with
  a printed NII line was obtained, so that corroboration covers the prior
  year only. Both quarters are used on a **standalone** basis — the
  consolidated results on p.9 of the Q1FY27 filing include large insurance
  subsidiaries and are not comparable with the other three banks.

  ICICI's gross and net NPA ratios are taken from footnote 1 on page 2
  (1.42% and 0.36% at 30-Jun-2026; 1.75% and 0.44% at 30-Jun-2025), which
  states them against **gross and net advances**. The ratios printed in the
  body of the table on page 1 (1.38% / 0.35% and 1.67% / 0.41%) are struck
  against **customer assets** — advances plus credit substitutes — a wider
  denominator the other three banks do not use. The advances-based footnote
  figures are the comparable ones and are what this project uses.
- **Kotak Mahindra Bank**: `KOTAKBANK_Q1FY26_deck.pdf` was downloaded but
  had a corrupted internal xref structure at the source (fails both
  pdfplumber's strict parser and a lenient pypdf re-parse past 26 of an
  expected ~38 pages) — dropped rather than special-cased into the
  pipeline. Not needed in the end: the **Q1FY27 deck's own "Bank
  Highlights" table (page 6) and balance sheet (page 8) already carry the
  Q1FY26 comparative column** alongside Q1FY27, so both quarters come from
  one verified file.

## Second extraction pass

The P&L components — other income, operating expenses and tax for all four
banks, in both quarters — were extracted once, then re-extracted a second
time independently, on 23 Sep 2026. The second pass located each table by
**content signature** rather than by the page number recorded the first
time, so a wrong page reference in the citation could not steer it back to
the same place, and the raw page text was read in full before any comparison
against `data/final/verified_inputs.csv` was made.

All 48 P&L values across the four banks matched on the second read. Two
corrections came out of the pass, both to documentation rather than data:
the claim that ICICI's two quarters came from different document types was
wrong, and the claim that no ICICI document prints an NII line was wrong.
Both are fixed above and in `LIMITATIONS.md`.

The pass also turned up each bank's own rounding disclosure — Axis states
"Certain amounts in the tables above may not add-up due to rounding off" and
HDFC states "Certain figures reported above will not add-up due to
rounding" — which independently supports the tolerance design in
`src/nim_bridge.py`, where the walk tolerance is derived from each bank's
printed precision instead of chosen.

## Scope note

This bridge covers four major private-sector banks (HDFC, ICICI, Axis,
Kotak Mahindra) comparing Q1 FY27 against Q1 FY26 (year on year, quarters
ended 30 June), all on a standalone basis. It is not a 12-quarter panel.

The method is a P&L-level attribution: the change in each bank's reported
profit is decomposed across net interest income, other income, operating
expenses, provisions and tax — five lines all four banks actually print.
Four reconciliation checks run before any comparison is written, and the
bridge is not produced unless all four pass. See
`data/processed/reconciliation_log.md` for the results, `reports/` for the
methodology writeup, and `LIMITATIONS.md` for what this deliberately does
not attempt — in particular the rate/volume/mix decomposition, which two of
the four banks do not disclose the inputs for.
