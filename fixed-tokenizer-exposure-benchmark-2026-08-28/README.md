# Fixed-tokenizer exposure benchmark

This benchmark holds Qwen 2.5 7B's tokenizer, base revision, 4-bit loading, prompts and deterministic
decoding fixed while comparing the base model with the already-frozen Ainglish development LoRA.
It measures exact registered-form recall from 19 newly authored marker-free glosses. A wrong first
answer triggers one authoritative register repair; the interaction cost counts the complete prompt
and continuation for every request, including repeated history.

Fifteen surfaces occurred in development training and measure exposure uptake. Four were
prospectively withheld when that adapter was trained and form a small exploratory transfer stratum.
Neither stratum is Ainglish governance evidence, and trained-surface recall is not independent
generalization.

Execution order:

```bash
python3 fixed-tokenizer-exposure-benchmark-2026-08-28/build.py
# Commit and publish items.json before either condition is run.
/home/dexagon/.venvs/ainglish-train/bin/python \
  fixed-tokenizer-exposure-benchmark-2026-08-28/run.py
```

The runner is offline-only: both the base revision and adapter must already exist locally.
