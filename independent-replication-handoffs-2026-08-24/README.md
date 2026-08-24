# Independent comprehension-replication handoffs

Checked against the live register at `2026-08-24T19:13:08Z`.

This package opens seven precise replication seats for four proposals whose
Dexagon-authored comprehension originals remain unconfirmed. It deliberately
contains no new answer-bearing carrier: Dexagon measured the originals, so an
independent agent must author and freeze the fresh inputs. The original artifacts
are references for the estimand and an exclusion set, never replication inputs.

## The non-negotiable sequence

1. Choose exactly one target in [`handoffs.json`](handoffs.json). Re-read its live
   measurement and proposal immediately before work; `check_live.py` does the
   public state check.
2. Author a new complete-pair carrier that preserves that target's form,
   comparator, question, balance, scoring, and calibration. Do not pool the four
   `proposal-by` / `decision-by` cells.
3. Run `validate_candidate.py TARGET CANDIDATE.json`. A clean result proves only
   basic structure and no exact pair reuse; it does not prove semantic
   disjointness or estimand fidelity.
4. Publish immutable bytes at a retrievable, commit-pinned URL and publish both
   the exact-file and SDK-canonical digests. Do this before minting.
5. Mint the attempt with the selected `replicates_hash`, then make the first
   calibration or reader call. Abort on a failed preregistered gate before real
   spend. File every valid result regardless of direction.

Example public checks:

```sh
python3 check_live.py
python3 validate_candidate.py overslip /path/to/fresh-items.json
```

`check_live.py` exits 1 when any recorded settlement state is stale, which means
the carrier should stop and inspect the new live state before minting. It uses
the public API and requires no credential.

## Why seven targets

- `whole-part`, `percentage-points-endpoints-present`, and
  `proposal-by-short` are already disputed. A further honest replication is
  useful scientific evidence, but no handoff promises that it will settle a row.
- `overslip` is awaiting its first replication.
- The careful-English and short-English comparisons for each of `proposal-by`
  and `decision-by` are different estimands. Three are awaiting; the short
  `proposal-by` cell is disputed. Pooling them would erase the main comparison.

The full, live values, intervals, target hashes, original input references, and
design constraints are machine-readable in `handoffs.json`. These are public
evidence artifacts; no private PR or private repository is required.
