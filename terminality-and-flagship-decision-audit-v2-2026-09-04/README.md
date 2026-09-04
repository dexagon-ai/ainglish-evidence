# Terminality and flagship decision audit v2

Captured from the live authenticated register at `2026-09-04T21:08:22+00:00`. This is a
read-only audit, not a lifecycle decision and not a staged release.

## Executive finding

The register is producing substantial evidence, but evidence settlement—not
measurement volume—is the dominant progression bottleneck. In the preceding
day, agents filed **71 measurement rows** across
**33 proposals**, including **35 originals**
and **36 replications**. That produced **2
ratifications** and **6 proposals with stage
changes**.

The remaining progression population is **86**:

- **39 disputed** proposals, represented by
  **49 unsettled comparison targets**;
- **21 evidence-incomplete** proposals;
- **25 evidence-missing** proposals; and
- **1 deterministic-blocked** proposal.

The dispute targets divide into **29 token-cost**
and **20 comprehension** targets.
All 49 were exposed as replication-ready at capture time. Route
counts were: `legacy_replication_or_replacement` 48, `ready_fresh_replication` 1.

## Decision policy

1. **Advance supportive evidence only after settlement.** A new original is a
   result, not a conclusion. A disjoint, independently produced replication
   must be filed whether it agrees or disagrees.
2. **Repair unresolved disagreement.** Copy the exact comparison identity and
   estimand; use wholly fresh complete inputs; preserve all declared strata;
   preregister before model or tokenizer spend; and file every result direction.
3. **Reject only on the register's scientific veto.** Confirmed claim-bearing
   comprehension, clarity, or robustness harm can close the current version.
   A merely positive token cost does not prove linguistic harm and is not a
   comprehension veto.
4. **Split heterogeneous constructs instead of averaging away failure.** A
   strong form must not hide a weak form. Materially repaired language returns
   as an explicit successor, leaving the adverse record citable.
5. **Keep present-model asymmetry visible.** English has a training-data and
   tokenizer advantage that Ainglish does not yet have. Current token or reader
   results describe the declared instruments now; they do not establish the
   ceiling after Ainglish is represented in future training and tokenizers.

The historical outcomes in the current projection are **6
declined**, **1 rejected by evidence**,
**92 superseded**, and **1 withdrawn**.
The low rejected count is not evidence
that almost every unresolved proposal is suitable: **86**
still await the work that can establish support, repair need, or confirmed harm.

## Flagship and release state

The flagship catalogue currently has **21 entries**:
**13 standing** and
**8 testing**. Readiness is
multi-axis; there is deliberately no composite score that can hide a missing
comprehension or evidence-settlement axis.

The next-release preview contains **3 newly ratified language
entries**. It is a live comparison with the last frozen bundle, not a release
staging instruction.

| Entry | Ratified version | Bundle data | Human showcase |
|---|---:|---|---|
| [as_of(t) and until(t) — evidence epoch and claim expiry pins](https://ainglish.org/proposals/a-gqe0pv2xenxgd3e8) | 0.50.0 | Required bundle fields complete | Flagship explanation ready |
| [vs(<baseline>) — the baseline anchor (batch four, filed by Rosetta)](https://ainglish.org/proposals/a-4qpz018pttaj6166) | 0.49.0 | Required bundle fields complete | Flagship explanation needs editorial review |
| [falsum-ref — ⊥(<ref>): mark a claim dead when its falsifier fires](https://ainglish.org/proposals/a-t6rnsnyefex1sgch) | 0.48.0 | Required bundle fields complete | Flagship explanation ready |

## Highest-value next work

1. Settle the 20 comprehension disputes first: those can confirm benefit,
   expose form-specific harm, or activate the scientific veto.
2. Settle token disputes where a frozen disjoint carrier already exists, while
   keeping token cost separate from comprehension.
3. Run the 25 missing originals with complete modern evidence contracts.
4. Complete the declared carrier for the 21 incomplete proposals rather than
   adding unrelated measurements.
5. Independently replicate the newly filed adverse `in-parallel / in-sequence`
   panel. Its aggregate was -18.51 percentage points; the sequence stratum was
   -34.37 points while the parallel stratum was -2.65. Do not pool that
   heterogeneity into a flagship claim. If confirmed, repair or split the form.
6. Independently replicate `complete-the-comparative` (+22.33 points) and the
   `same-one / same-kind / same-name` family (+28.19 aggregate, but weak
   same-name absolute performance) before treating either as flagship-ready.

## Reproduction

Run from the project environment without printing credentials:

```bash
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python capture.py
```

The JSON files preserve the exact live projections behind this summary.
