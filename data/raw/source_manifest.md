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
- **ICICI Bank**: the Q1FY26 deck (investor-presentation format, 59 pages)
  and Q1FY27 deck (regulatory results-filing format, 13 pages) are
  different document types from the same filer — a genuine format
  difference between the two periods, documented rather than smoothed over.
  Both carry a results table with Interest earned, Interest expended, Other
  income, Operating expenses, Provisions, Tax and Net profit. Neither
  prints a net interest income line: ICICI's NII is **derived** here as
  interest earned less interest expended, flagged `nii_source = derived`,
  and deliberately **excluded** from the `check_nii` tie-out, because
  checking a derived figure against the definition it came from would pass
  by construction. Both quarters of ICICI are used on a **standalone**
  basis — the consolidated results on p.9 of the Q1FY27 filing include
  large insurance subsidiaries and are not comparable with the other three
  banks.
- **Kotak Mahindra Bank**: `KOTAKBANK_Q1FY26_deck.pdf` was downloaded but
  had a corrupted internal xref structure at the source (fails both
  pdfplumber's strict parser and a lenient pypdf re-parse past 26 of an
  expected ~38 pages) — dropped rather than special-cased into the
  pipeline. Not needed in the end: the **Q1FY27 deck's own "Bank
  Highlights" table (page 6) and balance sheet (page 8) already carry the
  Q1FY26 comparative column** alongside Q1FY27, so both quarters come from
  one verified file.

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
