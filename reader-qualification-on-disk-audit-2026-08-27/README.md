# Existing-reader qualification audit

This is the terminal no-download sweep of the currently installed Ollama inventory. It maps every
local tag and digest to the retained v5, v7, v8, or v9 one-shot result before deciding whether a
GPU call is eligible.

The correct result is zero new inference: every installed distinct lineage either already failed
a frozen gate, is the sole qualified Qwen lineage, or is another edition of that same lineage.
Repeating observed cells would not be a fresh qualification, and another Qwen size cannot satisfy
the required second-lineage gate. Yi and LFM2 failures remain adverse results; neither is tuned or
retried.

The refreshed inventory also includes Solar Pro 22B. Its separately published prospective plan
failed the format stage with 12/12 HTTP 500 cells and exposed zero semantic items. This audit maps
that retained terminal transport result explicitly; it does not reinterpret the failure as a
semantic score or authorise a retry through a different adapter.

This audit intentionally records zero downloads and zero model calls. A future campaign needs a
genuinely new, prospectively selected installed lineage and a newly frozen disjoint qualification
holdout—not more GPU time on the current inventory.

The inventory was refreshed on 2026-09-03 after the overnight-work authorisation: all 53 installed
tags still collapse to 16 lineages, exactly one lineage remains qualified, and there are zero
fresh installed candidates. Consequently no additional scientific comprehension attempt can be
opened from local models without either retrying a consumed gate or lowering the evidence bar.

```bash
python3 reader-qualification-on-disk-audit-2026-08-27/audit.py
```
