# Existing-reader qualification audit

This is the terminal no-download sweep of the currently installed Ollama inventory. It maps every
local tag and digest to the retained v5, v7, v8, or v9 one-shot result before deciding whether a
GPU call is eligible.

The correct result is zero new inference: every installed distinct lineage either already failed
a frozen gate, is the sole qualified Qwen lineage, or is another edition of that same lineage.
Repeating observed cells would not be a fresh qualification, and another Qwen size cannot satisfy
the required second-lineage gate. Yi and LFM2 failures remain adverse results; neither is tuned or
retried.

This audit intentionally records zero downloads and zero model calls. A future campaign needs a
genuinely new, prospectively selected installed lineage and a newly frozen disjoint qualification
holdout—not more GPU time on the current inventory.

```bash
python3 reader-qualification-on-disk-audit-2026-08-27/audit.py
```
