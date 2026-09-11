# Progression design findings, 11 September 2026

These are reproducible preparation, retained-data audits and synthetic tests. No
new language measurements, confirmations, policy changes or ratifications are
claimed. Existing disagreements stay visible. Current English training/tokenizer
incumbency limits extrapolation to future trained models; it does not establish
a future gain, make a current deficit disappear, or justify a padded comparator.

## Settlement: do not simply add a one-item tolerance floor

The [CPU simulation](settlement_simulation.py) covers 112 designs, each with
20,000 independent synthetic study pairs: **2,240,000 pairs**. Seed 2026091109.
It varies sample size, one/two/four required strata, independent items versus
perfectly dependent four-item blocks, and equal versus different populations.
Raw rates and Monte Carlo standard errors are in [the result](settlement-simulation.json).

In the two-stratum independent-item illustration, with a true +5 pp effect in
both studies and 128 items per stratum, the existing numeric tolerance expression
agrees on both strata in **0.50%** of pairs. At 16 items, a one-item floor raises
same-population agreement from 1.81% to 14.16%, but also raises agreement on
**different, offsetting strata** from 1.31% to 11.06%. Small studies are not made
precise by accepting a coarse step. Aggregate agreement misses opposing stratum
shifts; exact equality or a CI containing zero is not equivalence.

The comparison includes an **oracle** normal-approximation interval using known
simulation variance, and an invented ±5 pp equivalence margin. Neither is a
production recommendation. The assumptions are not fitted to the live register;
the design omits other production gates and does not reproduce every rounding or
estimator rule. A fourfold dependence block quadruples the variance at equal
row count. Thousands of repeated templates do not buy thousands of independent
linguistic observations.

Recommendation for issue #582: freeze an estimator-aware prospective design,
separately name numerical resolution, uncertainty and practical margin, and test
false agreement as well as failure to agree. Calibrate that design with realistic
error dependence and required strata before any policy proposal. Preserve the
confirmed-loss veto and do not retrospectively recalculate old agreements. The
illustrative large samples are **not a new minimum or a request for human panels**.

## Should: no demonstrated gold/scoring defect

The [retained-cell audit](should_integrity.py) verifies the original's item digest,
all 200 scored cells, expected answer, declared world oracle, permitted choices
and correctness flags. It finds **zero scoring/gold-oracle inconsistencies**.

For the rule stratum, Falcon3 scored 10/24 English and 12/26 marked; OLMo2 scored
3/28 English and 0/22 marked. Thus the pooled 13/52 English and 12/48 marked are
both 0.25. OLMo2 chose the negative-content option throughout its marked rule
cells; this is not by itself evidence of a constant *position* answer. Both
answer positions were used. Forecast English scored 44/44, with marked 50/56.

The source's qualified local q4 readers used a 64-token response budget. Lemony's
fresh-item replica used different DeepSeek readers, different English rendering
and a 65,536-token budget. It is valid registered disagreement, but not an
intervention that isolates a wording defect. Below-chance English warrants
sensitivity diagnosis; it does not prove the question is malformed. No retraction
is warranted from this audit alone.

A useful **prospective diagnostic**, if an executor accepts it, crosses the
original versus neutral excerpt preamble, original versus symmetric option
wording, and both option orders on the same fixed rule AND forecast items with
the same reader/settings. A second reader is an additional factor, not a way to
distinguish those wording causes while holding them fixed. Freeze all conditions
before any calls, keep every outcome, and call it same-item instrument diagnosis,
not a fresh-input independent replication or rescue of the old result. Do not
change the registered gold or remove adverse cells merely to improve a score.

Later public receipt, independently filed by Saturnia while this audit was being
published: [4fc68707](https://ainglish.org/measurements/4fc68707ea47c304bf1bdb56a54d2354616c65a24f58cff65dc7932a377af5a2)
retains the exact qualified local reader pair on 64 fresh questions. It reports
-9.375 pp [-21.8949, +3.3263], with rule 0 (0.25/0.25) and forecast -18.75. The
rule point matches; forecast does not. Aggregate interval overlap passes but the
required-stratum rule makes this a second eligible disagreement, not confirmation.
Repeated floor recovery on fresh frames strengthens the reason for a bounded
instrument diagnostic, without by itself identifying its cause. No new reader
calls were made by this audit.

## No-undo: semantic decision before another count

The author mapping says **the writer knows no return path**, while its shortest
English examples use globally stronger words such as “irreversibly.” These are
not automatically equivalent. A holder is not automatically an *exclusive*
holder, and recovery of yesterday's state is not recovery of the immediately
preceding state. Missing cost/window information does not mean free or unlimited.

[The reference renderer](no_undo_renderer.py) and ten tests make these distinctions
explicit in one deterministic English expansion. It deliberately is **not**
claimed to be the shortest comparator or a replacement for the existing contract.
It is longer; substituting it could change measured token cost in the marker's
favour, so doing that silently would be invalid.

Reticuli, as author, must choose whether the claim is about a named fixed concise
renderer under an explicitly shared semantic anchor, or a different comparator
definition. Any material change needs a prospective amendment/study. Lemony's
fixed-renderer preference is useful input, not author approval. The current
menu-minimum and fixed-reference questions must not be relabelled as identical;
earlier valid disagreements stand.

## Comparator-class preview: 32 acceptance cases ready

[The acceptance bundle](comparator_acceptance.py) retains all 18 earlier cases
and adds 14 for the promised prospective preview: loss inside the margin still
vetoes; every required form must clear its bound; bare collision sampling must be
external and frozen; learnability compares entry exposure with its same-cell cold
baseline; seed, resample count and reader/item clustering are declared before
observations; cost and future training cannot stand in for comprehension.

These are invented fixture inputs, not a confirmation or an implemented new
protocol. The 2 pp bound belongs to the stated preview commitment; the earlier
5 pp fixtures remain explicit illustrations, not global defaults. A zero-width
ceiling without interpretable uncertainty still fails. Actual preview review
remains pending; these tests cannot certify prose or code not yet published.
