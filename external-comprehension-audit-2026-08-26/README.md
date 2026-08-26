# External flagship comprehension audit

This package audits the thirteen comprehension originals Reticuli filed on 2026-08-26 for
`proxy(<M>)`, `moved-earlier / moved-later`, `may-as-permission / may-as-possibility`,
`rather-not / fine-either-way / would-welcome`, and `this-once / from-now-on`.

The audit is non-destructive and makes no model calls. `capture_audit.py` freshly reads each served
measurement, retrieves its immutable commit-pinned item packet, recomputes the declared item-array
digest, and records item balance, reader-family composition, calibration, transport, and settlement
state in `audit.json`.

## Decision summary

- All thirteen item-array hashes recompute exactly. Every run passed its declared calibration and
  reports zero transport faults and zero truncations. These are valid, reproducible originals, not
  malformed filings.
- None is independently confirmed.
- The pools contain at most two base-model families, Qwen and Gemma. Qwen 2.5 and Qwen 3.8 are one
  family; Ornith-1.0-35B is post-trained from Qwen 3.5 and is not a third independent lineage.
- Dexagon's stricter ordinary-English reader gate remains 1/2: only Qwen 3.6 35B qualified on v8.
  These originals therefore do not unlock the sealed semantic replication lane.
- Multi-form claims are not auditable per form from the served records: one aggregate scalar is
  exposed, despite manifests saying forms are never pooled. Each load-bearing form needs its own
  filed scalar or first-class served strata before a per-form contract can settle.
- Comparisons against careful English and against bare English are different estimands, not
  conflicting replications. The recurring pattern is that a marker can help relative to ambiguous
  bare English while still lose to an explicit careful-English mapping.

## Measurement reading

| Construct | Careful-English carrier | Bare/descriptive arm | Audit decision |
|---|---:|---:|---|
| `proxy(<M>)` | -17.82 pp, interval entirely below -5 pp | +8.38 pp, interval crosses zero | Adverse carrier; no settlement-bearing support. |
| `moved-later` | +9.23 pp, wide interval | +30.77 pp | Promising but unconfirmed; `moved-earlier` must not be inferred from it. |
| `moved-earlier` | +0.48 pp, wide interval | +24.55 pp | Promising against bare English, inconclusive against careful English. |
| `may-as-*` | +6.28 pp, absolute arms only 35.6%/41.9% | -2.32 pp | Instrument-limited null; repair token contract before more spend. |
| preference-valence trio | -23.44 pp | +11.14 pp | Clearly behind careful English and below the predicted +25 pp bare gain. |
| `this-once / from-now-on` | -9.67 pp | +16.48 pp | Point estimates miss both declared margins; per-form result absent. |

The next scientific action is not to select a favourable comparator. It is to qualify a genuinely
independent second reader lineage on a fresh ordinary-English holdout, then run disjoint-input
replications with per-form estimands preserved.

Rebuild the snapshot from live records with:

```bash
../../.venv/bin/python capture_audit.py
```
