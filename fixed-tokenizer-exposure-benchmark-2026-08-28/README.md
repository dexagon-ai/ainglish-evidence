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

## Frozen result

Neither condition returned an exact registered form on the first pass: **0/19 base and 0/19
adapter**. Every item therefore incurred the authoritative repair turn. After that repair, the base
model reached **9/19** exact forms and the adapter reached **14/19**. The five changed cells all
moved from base failure to adapter success; none moved in the opposite direction. The trained-
surface stratum moved from 8/15 to 12/15, and the deliberately withheld four-item stratum moved
from 1/4 to 2/4.

Total interaction cost was 9,321 tokens for the base condition and 9,206 for the adapter, a reduction
of 115 tokens (1.2%). The paired median change was -4 tokens per item. That small change came from
shorter outputs and therefore shorter repeated history, not fewer turns. The fixed-tokenizer negative
control held by construction: both conditions used the exact same Qwen tokenizer and base revision.

The result is mixed. This small two-epoch adapter improved exact compliance *after* an authoritative
definition, but it did not eliminate a single definition/repair turn. It therefore supplies no
positive evidence for the strongest “training exposure removes accommodation cost” claim. It does
show why interaction cost and correctness must travel together: reporting only the 115-token saving
would conceal both the 0/19 cold result and the five additional correct completions.

Frozen result digest: `a688f7ec5c80de526a5281cae37dc6a3863cfdc8c5de16b033b02e790263e945`.
