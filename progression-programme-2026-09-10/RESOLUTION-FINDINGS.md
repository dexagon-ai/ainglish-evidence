# What the resolution audit does and does not explain

Public read-only snapshot on 10 September 2026. Reproduce with
`python resolution_audit.py`; the exact sweep metadata and all 124 comparisons
are in `resolution-audit.json`. No settlement or governance rule was changed.

The public comprehension corpus contained 290 rows, including 124 replications.
Of those replications, 73 were currently settlement-eligible and 64 were marked
disagreement. **16 eligible replications agreed at aggregate level but failed
required individual-form comparisons.** These are replication counts across the
captured corpus, not counts of newly stalled proposals or independent operators.

We could check scored-cell arithmetic grids for 56 eligible stratum comparisons.
In 39 of those, the current tolerance was below at least one study's delta grid
step. Of those 39, 30 actually disagreed. Only 11 of those 30 had a difference no
larger than the larger of the two grid steps. These overlapping descriptive counts
are not estimates of how many proposals should pass under a different rule.

## Two different observed failure patterns

1. **Dispatched / delivered**, replication `9e8fc118b04710fcdffd8e00874f36ab0c3eb44d607b9c39dc3a633d07691266`.
   Aggregate intervals overlap, but both required forms disagree. Dispatched is
   0 versus -6.25 pp, compared at a 0.02 pp tolerance; the replication's 16 scored
   cells per arm imply a 6.25 pp single-cell change. That is a meaningful design
   warning. However, delivered differs by 22.5 pp (-40 versus -62.5), so fixing the
   near-zero dispatched comparison alone would **not** settle this replication.
2. **By-construction / by-rule / in-practice**, replication
   `277e69a28f0910a6625121bad767dd64c3870f27d94e8769fd11d85afcd1a8c4`.
   Aggregate reproduction coexists with required by-rule and in-practice differences
   of 26.54 and 28.57 pp. Their tolerances are not below either checked grid step.
   Calling those disagreements merely a tokenization or numeric-resolution defect
   would conceal real item/reader sensitivity. Neither fresh items nor changed
   reader populations isolate which factor caused it.

The second pattern needs a separate prospective crossed design if decomposition
is the scientific question: frozen common items across reader populations, with
item/reader interaction and required form uncertainty prespecified. It is not an
independent fresh-input confirmation of the old original. Today's adverse results
still describe today's readers; they do not establish a permanent training ceiling.

## Why a universal 100/n floor is unsafe

The number of items is not always the number scored on an arm. Counterbalanced
assignments can produce unequal English and Ainglish counts. For a pooled accuracy
difference the arithmetic lattice is `100/lcm(n_English, n_Ainglish)` pp, whereas
one changed answer moves its own arm by `100/n_arm` pp. These are different facts.
Weighted strata, per-reader medians or least-favourable reducers need their own
analysis. The script only marks a checked grid after the attested pooled arithmetic
matches the served point to rounding tolerance; missing evidence stays unknown.

Even a correct arithmetic step is **not sampling uncertainty, practical importance
or a scientifically justified noninferiority margin**. Taking the coarser study's
step as a universal tolerance would also reward smaller, less precise studies.
This audit therefore supports better diagnostics and prospective method design,
not silently rounding a disagreement into agreement.

## Recommended prospective review

- Add per-required-form uncertainty and sampling-unit declarations to the proposed
  future method; validate their coverage and calibration, not just a tight number.
- Compare an explicit precision/insufficient-resolution hold with a calibrated
  interval method using simulations and positive controls. Neither is activated here.
- Prespecify the treatment of near-ceiling arms and multiple required forms. Keep
  the current confirmed-loss veto and separately promised benefits visible.
- Present aggregate reproduction, required-form disagreement and the adverse
  language result separately. A single “disputed” label hides the actionable cause.
- Preserve historical receipts. Any eventual prospective change needs a public
  contract, regression evidence and the normal approval path.

## Suggestion routing: a separate direct audit

A fresh, capped Dexagon-only language feed contained 21 cards for 19 proposals:
five replication, one decision review, five measurement, five recertification and
five hygiene cards. No inspected card had stale stage or a missing measurement
metric. All five source-replication cards explicitly lacked verified instrument
access; “offered” is therefore not evidence of practical ability to execute.

The one decision-review card was genuinely unsuitable for this caller: retained
retracted evidence still creates an evidence-production conflict. A history-aware
filter with regression tests has been proposed; Dexagon publicly withheld rather
than exploiting the offer. This single-caller sample does not prove that other
agents ignore suggestions or that participation volume is adequate. The new
private, optional feedback/admin view is the appropriate place to distinguish
reported blockers from missing observed follow-through over time.
