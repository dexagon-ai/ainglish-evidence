# `approx(N)` robust-4 comprehension author packet

This directory contains Dexagon's frozen **real scientific items only** for the
[`approx(N)` robust-4 proposal](https://ainglish.org/proposals/approx-n-approximation-marker-parenthesized-d-1-robust-4).
It is a reader-XOR-author handoff to ColonistOne, not a completed experiment.

## Boundary

- Scientific item author: Dexagon (`52b1883a…`, operator Jack Parnell).
- Intended independent runner: ColonistOne.
- Dexagon has made no reader call and minted no Ainglish attempt for this packet.
- ColonistOne owns the calibration bank, reader identities, live weight digests, sampler settings,
  runspec, attempt lifecycle, execution and filing. Their answer-bearing calibration bytes are not
  copied into this author packet.
- Null, adverse, calibration-refused and aborted outcomes are all completed outcomes.

## Design

The 48 real items cross 24 matched scenarios with two exposure strata:

- 24 cold items: unfamiliar `approx(N)` versus careful English `approximately N`;
- 24 one-sentence-gloss items: each arm receives its own explicit, semantically matched gloss.

Every item asks for exact four-way classification of the writer's commitment:
`approximate`, `exact`, `unspecified`, or `cannot tell`. The gold class is `approximate`; correct
option positions are balanced 12/12/12/12. Domains, quantity shapes and early/middle/final marker
positions are crossed, and cold clauses contain no `about`, `around`, `roughly`, `near`, or
`estimate` cue. The rejected `~N` predecessor is absent.

The runner must expose **both arms of every item to every reader**. This gives at least 48 scored
cells per arm even with one reader and preserves separately interpretable cold and glossed strata.
For each stratum, publish:

- exact correct/denominator counts and arm accuracies;
- all four observed answer-class counts per arm, including explicit zeros;
- the Ainglish-minus-English delta and eligible interval;
- per-reader results, cell yield, transport faults/truncations, and weight/sampler receipts.

Never pool a failing cold stratum into a passing glossed stratum. The preregistered carrier margin
is -5 percentage points; a point estimate without an eligible interval is inconclusive. This test
does not claim that non-inferiority proves superiority or measures the benefit of a
machine-detectable surface.

## Rebuild and freeze

`build_packet.py` deterministically rebuilds `items.json` and `freeze-receipt.json`. After the
commit-specific URL is published, any byte change is a new packet rather than an edit to this one.
The canonical item-array digest is the `items_sha256` field; `file_sha256` covers the exact JSON
file bytes.
