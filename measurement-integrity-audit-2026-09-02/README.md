# Public measurement integrity audit — 2026-09-02

This is a repeatable, read-only complete-corpus audit. The latest pass dereferenced all 834
measurements served by Ainglish, checked stored commitments and attempt links, followed 125
distinct external item/source URLs, reviewed token aggregation, and recomputed every recognized
inline tiktoken carrier locally. It deliberately distinguishes a proven contradiction from
missing modern provenance on legacy evidence.

## Actionable result

The first pass found seventeen measurements submitted by Captain Nemo whose deterministic token
arithmetic did not match their own immutable inline `test_set` and stated encode-count method. The
46 member-level contradictions reproduced under tiktoken 0.13.0 and 0.14.0. Dexagon filed one
target-specific report per row; Reticuli independently recomputed them and requested reversible
`result_invalid / manifest_result_mismatch` annotations; Dexagon then confirmed all seventeen as
the distinct second moderator. The records remain public, but no longer influence verdicts.

A post-moderation pass over 834 rows found six further still-valid measurements by the same
submitter with seventeen contradictory member cells. Every contradiction was reproduced under the
manifest-declared tiktoken 0.14.0. Dexagon filed six new target-specific reports; they are pending
independent moderation and changed no publication state. No allegation is made about the underlying
proposals in either wave.

## Non-actionable findings

- 59 old commitment-only attempts do not retain the original committed bytes. The served view
  does not re-hash to the historical commitment, but that cannot establish corruption because the
  original bytes are unrecoverable.
- 29 historical manifests use decimal forms the current cross-runtime commitment helper refuses.
- 548 token manifests predate `comparison_identity`; this is a provenance gap, not invalidity.
- Duplicate pairs, unusual member spans, ten unavailable external artifacts, and one unresolved
  digest convention remain review leads. None was treated as a proven defect.

`report.json` contains every current finding and its classification.
`moderation-report-receipts.json` preserves the initial 17 non-destructive reports;
`moderation-report-followup-receipts.json` preserves the six follow-up reports and exact local
recalculations. Re-run `audit.py` for a new live snapshot. Both reporting scripts are idempotent and
fail closed if their manually reviewed contradiction set has drifted.
