# Semantic conflict and duplication atlas

Status: candidate builder and review-only classifier runner prepared. No model output has yet been
treated as a register relation. The final atlas will keep every row `review_required: true` and
`asserted_relation: null` even when both classifier families agree.

The classifier writes one fsynced review card per pair to `classifier-ledger.jsonl`; interrupted
review-only runs resume completed cards rather than silently losing hours of GPU routing work.
