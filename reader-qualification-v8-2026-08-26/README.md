# Reader qualification v8: prospective structured-output branch

This package is an instrument-qualification campaign, never Ainglish proposal evidence. It
responds to the terminal v7 no-roster result without rescoring or rerunning any v7 cell.

Four already-acquired, mutually distinct model families enter one fixed development screen:
Mistral Small 3.2 24B, Gemma 3 12B, EXAONE 3.5 32B, and Phi-4 14B. Every candidate first passes
the frozen 12-cell format-only JSON-schema gate. A passing candidate then sees the already-exposed
24-cell ordinary-English development packet from `reader-qualification-calibration-v1-2026-08-26`.
There is no prompt tuning between candidates and every result, including failures, is retained.

A fresh v8 holdout may be authored only if at least two distinct families pass the prospective
development gate: 24/24 schema-exact responses, at least 22/24 correct, at least 2/3 per semantic
axis, at least 7/8 per answer label, zero thinking bytes, and zero faults. Development success does
not qualify a reader. Qualification requires a later digest-pinned, disjoint holdout committed and
pushed before its first model call.

Build the frozen candidate plans with:

```bash
python3 build_development_plans.py
```

The generic staged runner and auditor live in `reader-fresh-lineage-v1-2026-08-26`; the plans bind
their prompt, transport, gates, local model manifests, Ollama version, and upstream packet digests.

## Primary development outcome

All four primary candidates passed the strict structured-output gate. Phi-4 alone passed the
semantic development gate at 23/24. Mistral and EXAONE scored 20/24; Gemma scored 19/24. The three
failures concentrated on `not determined`, and no score or key was changed after observation.

Because only one lineage passed, no qualification holdout was authored. A single already-installed
high-capacity Qwen 3.6 35B reserve is frozen separately before use. It advertises optional thinking,
so its plan permits that capability only while the request transmits `think: false`; any returned
thinking byte fails the unchanged gate. The reserve uses the same prompt, packet, thresholds, seed,
and JSON schema as the four primary candidates.

