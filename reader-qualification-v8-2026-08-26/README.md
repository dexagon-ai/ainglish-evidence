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

Qwen passed that reserve development screen at 24/24, with 8/8 on every label and zero thinking
bytes. Phi and Qwen therefore entered a newly authored 64-item qualification holdout covering eight
ordinary-English semantic axes. The holdout has zero exact premise/hypothesis overlap with all prior
qualification JSON in this repository, contains no Ainglish target construct, balances opaque answer
positions 22/21/21, and is committed before either qualification call. Passing requires 64/64 exact
schema responses, at least 60/64 correct, at least 7/8 on every axis, zero thinking bytes, and zero
faults; both lineages must pass before any scientific roster is released.

## Terminal qualification outcome

Qwen qualified at 61/64, with every axis at least 7/8, 64/64 exact schema responses, zero thinking
bytes, and zero faults. Phi scored 58/64 and fell to 6/8 on both conditional and reference-resolution
items, so it did not qualify. The two-lineage rule therefore failed: `selected-result.json` records
`roster_ready: false` and an empty fixed roster. No scientific flagship carrier was exposed, minted,
or run from v8. The single Qwen pass is retained as an instrument result, not promoted into a panel.
