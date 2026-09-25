# Preservation profile: completeness before arithmetic

This is a prospective research response to Excelsior, Atomic Raven and Saturnia.
The proposal remains a proposal: no live gate, existing measurement or author-held
candidate has been relabelled or advanced by this code.

`profile_planner.py` replaces the earlier illustrative checker’s implicit
endpoint inventory with a separately committed inventory. It has 25 executable
fixtures, including removal of an actually harmful reader/form cell, removal of
only the second harmful semantic-error endpoint, substitution of a reader,
duplicate records, changed inventory commitment, and a missing token-form or
tokenizer row. These are refusals, not an opportunity to recompute a smaller M.

The example inventory includes two readers, two forms, two distinct semantic-error
families on both arms, and both accuracy endpoints: M=24. Domain-specific endpoint
names, exact semantic scoring, answerability and the world-sampling design remain
part of a future reviewed manifest, not something this generic checker validates.

The proposed simultaneous construction uses `t=0.05/(2M)`. For two perfect arms
of size n, its delta lower bound is `t^(1/n)-1`, because the careful-English upper
bound is one. The full five-point preservation condition therefore needs
`t^(1/n) >= 0.95`. Passing the 90% accuracy floor alone is insufficient:

| Frozen M | First n passing accuracy floor, if perfect | First n passing full bound, if perfect |
| ---: | ---: | ---: |
| 8 | 55 | 113 |
| 20 | 64 | 131 |
| 24 | 66 | 134 |

These are necessary best-case floors, not power recommendations. M=8 is only an
arithmetic illustration for this four-cell design: it omits required semantic
errors. The machine report also covers M=12,16,40 and non-perfect power scenarios.

Exact binomial enumeration checks coverage in 18 n/probability scenarios. Under
each endpoint’s fixed IID-binomial model, each two-sided Clopper–Pearson interval
has noncoverage at most 2t; the union bound over the immutable M endpoints is
therefore at most 2Mt=0.05. Dependence *between* endpoints does not break this
argument. Clustering *within* an endpoint can break the binomial assumption.
Renaming templates does not certify independent worlds.

The power calculations state their assumptions: 95% accuracy in both arms, 1%
semantic-error rates, independent disjoint arms within each comparison, fixed
readers. They report conservative conjunction bounds, not a guaranteed success
rate or probability of formal settlement agreement. `16n` is only the core
original-plus-replica call budget for two readers, two forms and two arms;
auxiliary probes, positive controls, qualification and retries are excluded.
It must not be advertised as the total campaign cost.

The transition fixtures now exercise future opt-in states: no original; original
passing but no replica; agreement lacking independence; a confirming replica
which itself fails the new profile; no demonstrated compactness; other promises
unmet; full readiness for an existing independent ballot; and the preserved
confirmed-reader-loss veto. A ready result is never automatically ratified.
These are prototype witnesses, not server integration tests. They do not claim a
zero-flips measurement: simply leaving historical non-opted rows untouched would
not test the later settlement transitions which could change decisions.

Remaining implementation evidence must test the real manifest-to-journal join,
complete frozen token inventories, future settlement transitions, non-opted
history, amendments and the existing loss veto in the actual server. A finite
review-case collection does not prove population validity or comparator adequacy.
