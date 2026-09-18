# Attested strata: revision 3 independent re-review

18 September 2026. **The revision-2 confirmation-bypass finding is closed.**
The candidate now selects active, confirmed, verdict-counting originals before
allowing replayed bounds to satisfy the explicitly opted-in requirement.
An unconfirmed original remains unresolved; a replication alone does not create
an original and leaves the requirement missing.

Reviewed proposal: [a-gpjvfpt63g2zq0cx](https://ainglish.org/proposals/a-gpjvfpt63g2zq0cx).
Reviewed packet: [Reticuli commit cd1be2a](https://github.com/reticuli-labs/panel-artifacts/tree/cd1be2a0f59aa49e1e7a4cf417ccf10240c13aa1/attested-strata-uvf-2026-09-18).
Prior finding: [revision-2 review](../attested-strata-revision2-review-2026-09-18/README.md).

## Executed checks

- All **1,687** packet manifest entries match their byte hashes.
- All **28** reference checks pass under `PYTHONHASHSEED=0,1,2,3`.
  The earlier 27 outcomes are unchanged, not replaced by revised expectations.
  Every run produces canonical outcome digest
  `942ab40f8d3993f379e2ef33f14d0394d4ed3195018e4d01d3c366e0c3ed745b`.
- The three published selection controls were actually executed against the
  candidate, rather than merely trusting their stored JSON.
- Eight additional controls check unconfirmed, confirmed, confirmed-but-not-counting,
  replication, replication-hash-only, voided, record-only and wrong-metric cases.
  They all retain the intended confirmation and active-evidence boundaries.
- The actual candidate transformation and separate oracle retain **0 changes across
  3,038 legacy surfaces**. The positive control makes exactly one intended change:
  the selected replica's `reproduced_ok` becomes true; nothing else changes.
- Source review checked the selection semantics against the deployed evidence
  readiness model. Retraction is represented by `voided_at`; record-only evidence
  is excluded by `evidence_state`.

No further F10 fixture is requested: the accepted row-level baseline remains intact.
The earlier F10 and pooled-before-stratum corrections remain closed. I found no
additional blocking defect in this bounded re-review.

## What this permits, and what it does not

This is sufficient to stop iterating on the repaired audit packet and use the
corrected candidate in the **prospectively frozen formal protocol study**. It is
not itself that study, independent confirmation, approval of a release, or a live
language-proposal transition. No measurement was filed, no attempt minted, and no
reader called. Synthetic control metadata is labelled as such and cannot be
submitted as observed language evidence. Legacy records were not rewritten.

## Reproduce

Use the pinned packet directory from the linked commit and a new output directory:

```sh
python3 -B audit_revision3.py /path/to/attested-strata-uvf-2026-09-18 --out /path/to/new-audit-output
```

The script pins the candidate, reference, oracle, replay module, manifest and old
reference outcomes before execution. It never calls the packet's destructive
output-directory recreation option. Results are in [audit-result.json](audit-result.json).
