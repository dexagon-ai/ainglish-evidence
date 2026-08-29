# Universal-negation comprehension carrier v2

This explicit v2 repairs the three activation blockers found after independent agents seconded
`none-of(<S>) / not-all-of(<S>)`. It does not rewrite either frozen v1 packet.

Each of the zero-shot and definition-conditioned packets contains:

- the 160 v1 semantic rows, byte-for-byte preserved after removing the two new question records;
- a separately scored `rely_on_one_satisfier` consequence probe;
- a separately scored `N-1` compatibility control;
- 100 new validity rows, balanced across both forms and five set states: empty, missing, changing
  without an epoch, multiply resolved, and a fixed non-empty receipt-and-epoch control;
- 12 construct-free calibration rows.

The seven seam and validity gates are evaluated per qualified reader lineage and condition. A
pooled score cannot override any failed gate. Invalid sets must be classified as invalid or
unresolved and assigned no quantifier interval; in particular, an empty set never receives a
vacuous `none-of` truth. The fixed receipt-and-epoch rows prove that a reader is not merely
rejecting every use.

Zero-shot performance measures present transparency for readers that were generally trained on
English rather than Ainglish. Definition-conditioned performance measures one-card learnability.
Neither is presented as future pretrained efficiency, and neither can rescue a failed gate in the
other condition.

## Freeze and audit

The live snapshot was captured before any attempt or reader call. Rebuilding is deterministic
from that snapshot, the independently reviewed v1 digests, and the activation-review digest.

```bash
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python \
  universal-negation-carrier-v2-2026-08-29/capture.py

/home/dexagon/codex/dexagon/.venv/bin/python \
  universal-negation-carrier-v2-2026-08-29/build.py

/home/dexagon/codex/dexagon/.venv/bin/python \
  universal-negation-carrier-v2-2026-08-29/audit.py
```

Do not run a scientific cell until one published runspec binds these exact packet bytes and two
independently qualified base-model lineages from families outside the original panel. Mint the
exact manifest before calibration or scientific spend, retain every finite/null/adverse outcome,
and never treat the definition-conditioned packet as confirmation of zero-shot comprehension.

No model or tokenizer was called, no attempt was minted, and no governance measurement was filed
while producing this freeze.
