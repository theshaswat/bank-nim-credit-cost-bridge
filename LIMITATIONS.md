# Limitations

Stated plainly, not hedged into vagueness.

## One year-on-year comparison cannot separate a credit cycle from a provisioning cycle

This is the limitation that matters most, because it bears directly on the
project's main finding. Provisions fell at all four banks and contributed
most of the profit growth at three of them. The gross NPA ratio also fell at
all four, which supports reading that as a genuine improvement in the book
rather than a decision to provide less.

But two quarters twelve months apart cannot settle it. A bank running down a
provision buffer built in an earlier cycle and a bank whose borrowers are
genuinely repaying better will both show falling provisions against falling
NPAs for several quarters. Distinguishing them needs the provision coverage
ratio and a slippage series across more quarters than this project covers.
The finding here is what the disclosed figures support; it is not proof that
the improvement persists.

## Not a rate/volume/mix decomposition

The original plan was a three-factor decomposition of the NII change into
rate, volume and mix effects — standard for a bank margin bridge. It is not
attempted, and the reason is specific rather than general.

That decomposition needs yield on assets and cost of funds for both periods.
HDFC and Kotak publish those only as labels inside chart images in their
decks, with no reliable position-to-label correspondence available to
plain-text extraction. Axis and ICICI publish a clean interest
income/expended table, which is enough for NII growth but not for the
yield/cost split either. A decomposition built on two banks' real numbers and
two banks' guessed ones would look complete and be half-fabricated.

What replaced it — a P&L-level attribution of the change in profit across
NII, other income, opex, provisions and tax — uses only figures all four
banks actually print, and reconciles to each bank's reported bottom line.
It answers a coarser question than rate/volume/mix would have, and it answers
it on real numbers.

## Not a panel regression

Four banks, two quarters: eight observations. No regression, no clustered
standard errors, no p-values anywhere in this project.
`indfin.stats.wild_cluster` exists for a project that actually has a panel;
running it on eight observations would produce a statistic with nothing
behind it.

## What is genuinely not disclosed

Three gaps, all real, none worked around with a secondary source:

- **ICICI publishes no net interest margin and no credit-cost ratio** in
  this filing. Those two cells are empty for ICICI and it is excluded from
  the margin-vs-credit-cost exhibit, which the chart states on its face.
- **ICICI's regulatory filing prints no NII line.** Its NII is derived here
  as interest earned less interest expended, flagged `nii_source = derived`,
  and excluded from the arithmetic tie-out — checking a derived figure against
  the definition it was derived from would pass by construction and prove
  nothing. For Q1 FY26 there is an external check, and it holds: ICICI's own
  Q1 FY26 investor presentation prints standalone NII of ₹216.35 bn on page 7,
  against ₹21,634.46 Cr derived here from the regulatory filing — a difference
  of ₹0.54 Cr, 0.002% of the figure. That corroboration does not extend to
  Q1 FY27, where no ICICI document carrying a printed NII line was obtained,
  so the Q1 FY27 derivation rests on the filing alone.
- **HDFC and Kotak publish NII but not the interest income/expended split**,
  so their NII cannot be tied out arithmetically either. Both are covered by
  reconciliation check 2 instead, against growth percentages they publish
  themselves.

An earlier revision of this project claimed considerably more was undisclosed
than actually is. That was under-collection rather than a disclosure limit,
and it was corrected: all four banks do publish NII, and all four publish a
gross NPA ratio.

## Measures that are not comparable across banks

- **Credit-cost levels.** HDFC reports gross of recoveries, Axis reports net
  credit cost annualised, Kotak reports specific provisions only. Within-bank
  change is comparable; the level across banks is not, and no exhibit places
  those levels side by side.
- **Advances.** HDFC publishes average advances under management, Kotak
  publishes period-end net advances. Recorded with an explicit
  `advances_basis` column rather than pooled into one series.
- **Net interest margin.** Each bank computes it on its own asset base. The
  change is the meaningful comparison, not the level.

## HDFC's reporting precision

HDFC publishes its standalone income statement in ₹ billion to one decimal,
so each line carries up to ±₹5 Cr of rounding. Its P&L walk closes to within
₹10 Cr and its attribution to within ₹20 Cr, both inside bounds derived from
that precision and both recorded explicitly in `rounding_residual_cr` rather
than absorbed. The other three banks close exactly or to within ₹1 Cr.

## Source-document asymmetry

Both ICICI periods are taken from one document — the 13-page Q1 FY27
regulatory results filing, which carries the Q1 FY26 comparative column for
every P&L line used here. An earlier revision of this file described the two
periods as coming from different document types; that was wrong. ICICI's
Q1 FY26 investor presentation is kept in `data/raw/` for one purpose only:
the independent NII corroboration noted above.

`KOTAKBANK_Q1FY26_deck.pdf` downloaded with a corrupted internal xref
structure — it failed pdfplumber's strict parser and a lenient pypdf
re-parse recovered only 26 of roughly 38 pages. Rather than add a second
parser to the pipeline for one file, it was dropped. The gap turned out to be
moot: Kotak's Q1 FY27 deck carries the Q1 FY26 comparative column for every
figure this project needs. The corrupted file is not in this repository.

## What this project does not claim

It does not rank the four banks on overall performance, does not forecast
forward margin or credit cost, and does not attribute a cause to any
movement the disclosed figures cannot support. Where the attribution shows
a large swing driven by a one-off — HDFC's other income is the clear case —
the one-off is named rather than absorbed into a narrative about the
underlying business.
