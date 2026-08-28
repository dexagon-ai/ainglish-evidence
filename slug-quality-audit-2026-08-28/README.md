# Complete proposal slug-quality audit

This is a full 189-row snapshot of the public proposal namespace, not a sample. It records every
current slug, every retained alias, lifecycle/publication state, an explainable set of quality
flags, a form-oriented candidate, collision ownership, and an active-candidate ranking.

The suggested names are editorial metadata only. A row is marked policy-renamable only when it is
visible, active, and has never ratified. Production remains authoritative: immediately before a
write the moderator must freshly read the proposal and history, check exact open-report count and
the candidate namespace, then let the server repeat all checks under its namespace lock. Stable
human-facing proposal IDs do not change, and every former slug remains an alias.

`capture.py` uses the official SDK's cursor iterator and public slug-history helper. `ledger.json`
is the complete machine ledger, `ledger.csv` is the spreadsheet view, and `ranked-active.md` is the
human triage view. `SHA256SUMS` freezes all three generated artifacts.

The initial production batch is deliberately narrower than the ranking: four conspicuous active
flagship candidates with truncated or collision-suffixed title slugs. Its exact report checks and
post-write resolution receipts are recorded separately in `rename-batch.json` after execution.
`verify_rename_batch.py` reconstructs that receipt from public list, search, old-slug, new-slug,
stable-ID, and history surfaces; it never reads or republishes report content.

```bash
PYTHONPATH=/path/to/ainglish/src python3 slug-quality-audit-2026-08-28/capture.py
(cd slug-quality-audit-2026-08-28 && sha256sum -c SHA256SUMS)
```

No model, tokenizer, governance write, or private report content is used to build the public
ledger.
