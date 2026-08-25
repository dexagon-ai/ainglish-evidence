# Flagship one-shot reference-loaded comprehension

This campaign measures a deployment condition that the cold standalone flagship originals did not:
both arms first receive the same concise reference card defining the relevant marker pair. The
Ainglish arm then uses the compact marker; the comparator uses its complete careful-English meaning.

This is a separate post-ratification diagnostic. It will not overwrite the cold results, claim that
models knew Ainglish from training, or turn two local readers into independent evidence principals.

The eight form-specific carriers contain 64 fresh scientific pairs and eight construct-free
calibration rows apiece. Each result stands alone; a favourable form cannot conceal an adverse
partner. Null and adverse outcomes are filed without retry.

Freeze and execution order:

1. Build and inspect the answer-bearing item files with `build_items.py` (zero reader calls).
2. Commit and publish them, then bind runspec URLs to that immutable commit with
   `build_runspecs.py --items-commit <full-sha>`.
3. Commit and publish the runspec index.
4. Start a dedicated digest-pinned reader on GPU 0 and run `run_all_once.py` exactly once.

Current status: 512 scientific pairs and 64 calibration rows are frozen with receipt digest
`ce3a221afb1dd5b124b8b04e5529c3b2a5ab46b068bce1182ee7071d626991fc`. The eight runspecs bind
those bytes to public item commit `35745cd7fc47e08e6ff4ef14e781d1a91f84d2e2` and their sealed
index has digest `d1745ef072bc60bfe68eb17dd43d27514d90e63ab73bba7b889c7da535ffff8e`.
All eight passed the released SDK's zero-cost dry-run. No real reader call or attempt mint has
occurred.
