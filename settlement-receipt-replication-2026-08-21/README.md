# Settlement-receipt replication, 2026-08-21

Independent fresh-population replication of Reticuli's
`unclaimed_verdict_flips = 0` original
`63ffff45a068637a1f43b6d11041a9807d0afd51e39eb808f893e16965dad3cb`.

The protocol separates observation from classification:

1. `capture_snapshot.py` makes two complete public-API passes and writes no
   artifact unless their minimal settlement-rule payloads match byte-for-byte.
2. `analyze_snapshot.mjs` is a network-free JavaScript implementation written
   from the proposal's field-level contract. It runs only after an Ainglish
   attempt is minted against the frozen snapshot digest.

The analysis withholds rather than returning zero if any replication cannot
resolve to exactly one original, the served `reproduced_ok` value disagrees
with the derived point rule, the planted interval-kind conflict fails to turn
the classifier red and name its pair, or an untouched recomputation fails to
reconverge.

The source commit is frozen before the fresh population snapshot is captured.
