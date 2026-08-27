# Public evidence-corpus snapshot v1

This directory freezes one max-id/keyset cursor sweep of the complete public Ainglish measurement
index, followed immediately by each included row's attempt record. Where the server exposes an
immutable attempt-manifest receipt, its exact bytes are retained; legacy fallback rows are marked
separately. The bundle contains no private API data and performs no governance write.

The index cursor freezes membership against concurrent inserts. It does not freeze later moderation
or voiding changes; `records.jsonl` therefore pairs the complete index row observed at capture with
the exact JCS manifest bytes committed by its attempt. Exact bytes are retained as the
`manifest_jcs` string, so legacy numeric encodings remain hash-verifiable instead of being silently
normalised by a modern serializer. The oldest backfilled attempts have no stored-manifest receipt;
for those rows the bundle preserves the live permalink response, marks the manifest hash as
unverified, and never upgrades a parsed reserialization into an exact-byte claim.

Attempt id—not manifest hash—is the row identity in this bundle. Historical same-manifest build
checks can share a hash with their original, making the hash permalink resolve only one of the two
rows. `MANIFEST.json.manifest_hash_collisions` records every such case rather than silently
deduplicating it.

Capture requires the snapshot-safe SDK surface proposed in `ai-nglish/ainglish#103`:

```bash
PYTHONPATH=../worktrees/sdk-measurement-index-20260827/src \
  python3 evidence-corpus-snapshot-v1-2026-08-27/capture.py
PYTHONPATH=../worktrees/sdk-measurement-index-20260827/src \
  python3 evidence-corpus-snapshot-v1-2026-08-27/verify.py
```

No model was called or downloaded.
