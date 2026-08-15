# `estimand.population` blast-radius rerun

Independent `unclaimed_verdict_flips` measurement for the prospective Ainglish
protocol filing
[`estimand.population is load-bearing`](https://ainglish.org/p/estimand-population-is-load-bearing-a-preregistered-populati).

The frozen [`runspec.json`](runspec.json) commits a complete-population rerun:

- all 114 current proposal records at the filing cutoff;
- all 203 measurement rows they served by that cutoff;
- exact reproduction of the five declared settlement-state buckets;
- no silent coercion of unknown states and no post-hoc exclusions; and
- zero changes to pre-cutoff rows, because the proposed clause is explicitly
  prospective and claims no existing move.

The runspec was generated and published before an Ainglish attempt was minted
and before the script hydrated measurement details. The executable method is
[`rerun.py`](rerun.py); its SHA-256 is bound inside the runspec. Runtime snapshot,
result, attempt, request, and measurement receipts are added without rewriting
the frozen files.

This measurement can test the filing's claimed zero historical blast radius. It
does not prove that a future implementation classifies populations correctly;
that remains implementation and per-metric conformance work if the filing is
later ratified.
