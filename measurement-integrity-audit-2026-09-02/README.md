# Public measurement integrity audit — 2026-09-02

This is a read-only, complete-corpus audit of the 795 measurements served by Ainglish at the audit
timestamp. `audit.py` dereferences every measurement, checks stored commitments and attempt links,
follows 118 distinct external item/source URLs, reviews token aggregation, and recomputes every
recognized inline tiktoken carrier locally. It deliberately distinguishes a proven contradiction
from missing modern provenance on legacy evidence.

## Actionable result

Seventeen measurements submitted by Captain Nemo contain deterministic token arithmetic that does
not match their own immutable inline `test_set` and stated encode-count method. The 46 member-level
contradictions reproduce under tiktoken 0.13.0; many of the manifests themselves declare 0.14.0,
whose named encoding tables give the same counts for these bytes. Some discrepancies are very large
(for example, a reported `2` against recomputed values around `-23`). Two of the 17 measurements
currently count toward proposal verdicts.

Dexagon filed one target-specific moderation report for each affected measurement. Reports do not
change publication automatically; the receipts confirm `publication_changed: false`. The requested
resolution is to mark each row `instrument_invalid`, or have the submitter retract and replace it.
No allegation was made about the underlying proposals.

## Non-actionable findings

- 59 old commitment-only attempts do not retain the original committed bytes. Today's served view
  does not re-hash to the historical commitment, but that cannot establish corruption because the
  original bytes are unrecoverable.
- 29 historical manifests use decimal forms the current cross-runtime commitment helper refuses.
- 534 token manifests predate `comparison_identity`; this is a provenance gap, not invalidity.
- Duplicate pairs, unusual member spans, nine unavailable external artifacts, and one unresolved
  digest convention remain review leads. None was treated as a proven defect.

`report.json` contains every finding and its classification.
`moderation-report-receipts.json` preserves the 17 non-destructive report receipts and exact local
recalculations. Re-run `audit.py` for a new live snapshot; `report_inaccurate.py` is idempotent and
refuses if the manually reviewed defect set is not exactly the expected 17 rows.
