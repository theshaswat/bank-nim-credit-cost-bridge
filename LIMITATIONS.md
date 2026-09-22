# Limitations

Stated plainly, not hedged into vagueness.

## Not a rate/volume/mix decomposition

The original plan for this project was a three-factor decomposition of NII
change into rate effect, volume effect, and a mix/interaction term —
standard practice for a bank margin bridge. It's not attempted here. The
reason: HDFC and Kotak disclose average balances and a headline NIM%
directly, but their yield-on-assets and cost-of-funds figures — the two
inputs a rate/volume/mix split actually needs — exist only as chart labels
in their decks, and plain-text PDF extraction can't map those labels to
values unambiguously (the numbers sit in a chart, not a table, with no
reliable position-to-label correspondence). Axis and ICICI do disclose a
clean enough interest income/expense table to compute NII growth, but not
the yield/cost-of-funds split either. A decomposition run on two of four
banks' real numbers and two banks' guessed numbers would look complete and
be half-fabricated — not attempted, for that reason specifically.

## Not a panel regression

Four banks, two quarters. That's 8 observations, not a panel with enough
degrees of freedom for any regression-based inference. No wild-cluster
bootstrap, no clustered standard errors, no p-values anywhere in this
project — `indfin.stats.wild_cluster` exists as a general-purpose module for
a project that actually has a panel (e.g., more quarters, more banks), but
running it here would produce a statistic with no real meaning behind it.

## Incomplete rows are a feature, not a gap to paper over

The summary table has blank cells for every metric a bank doesn't disclose
in a form this project could independently verify:
- Only Axis and ICICI have `nii_growth_yoy_pct` (they're the only two
  disclosing Interest Income/Expended separately, which is what lets NII be
  tied out against the bank's own reported figure via `indfin.check_nii`
  rather than trusted blindly).
- Only HDFC and Kotak have `nim_change_bps` and `gnpa_change_bps`.
- Only Kotak has `credit_cost_change_bps`.

No secondary source was used to fill any of these in. A complete-looking
table across all four banks on all six metrics would have required pulling
figures from somewhere other than each bank's own primary disclosure for
that quarter, which would break this project's core standard (every number
traceable to a specific, cited page of the bank's own filing).

## Basis asymmetry

- **ICICI Bank**'s two source decks are different document types: Q1FY26 is
  a full investor presentation (59 pages), Q1FY27 is the shorter regulatory
  results filing (13 pages). Both carry the same results-table structure and
  both tie out via `check_nii`, but it's a genuine format difference between
  the two periods being compared, not an oversight.
- Basis (standalone vs. consolidated) is noted per-row in
  `verified_inputs.csv` rather than normalized — see `DATA_DICTIONARY.md`.

## Kotak Q1FY26 source file

`KOTAKBANK_Q1FY26_deck.pdf` downloaded with a corrupted internal xref
structure — failed both pdfplumber's strict parser and a lenient pypdf
re-parse (recovered only 26 of an expected ~38 pages, and the recovered file
still failed the stricter parser downstream). Rather than add a second PDF
parser to the pipeline to accommodate one file, it was dropped. The gap
turned out to be moot: Kotak's own Q1FY27 deck (`page 6`, "Bank Highlights"
table, and `page 8`, balance sheet) already carries the Q1FY26 comparative
column, so both quarters in this project come from one verified file. The
corrupted file itself is not included in this repository.

## What this doesn't claim

This project doesn't rank the four banks against each other on overall
performance, doesn't forecast forward margin or credit cost, and doesn't
attribute causes to any bank's NII-vs-PAT gap that the disclosed figures
can't actually explain (see the memo's Axis Bank section, where NII growth
alone doesn't account for PAT growth and the memo says so rather than
guessing which other line did).
