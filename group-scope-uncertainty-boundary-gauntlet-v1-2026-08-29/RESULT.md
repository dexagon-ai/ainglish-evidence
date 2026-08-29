# Result

All 12 frozen batches were valid and all 144 cells were correct: 48/48 for each of Qwen 3.5 9B,
Gemma 3 12B, and Mistral Small 3.2 24B. Both forms, all four boundary families, and all three
evidence states scored 100% separately. There were no transport faults, invalid batches, answer
omissions, or thinking bytes.

Most importantly for the review objection, all 48 marker-only cells were handled correctly. The
readers did not infer a named significance test, interval exclusion, equal effect magnitude, or
low variance merely from `each-group` or `groups-combined`. They also followed explicit positive
and negative statements on those axes.

This is a narrow supplied-reference result. The prompts stated the boundary explicitly and the
positive/negative controls were deliberately clear. It shows that the proposed separation between
aggregation scope and uncertainty can be applied by these three readers when taught; it does not
show cold comprehension, real-world statistical validity, human understanding, independent
evidence, or ratification readiness.

The first execution request stopped before any model call because a 512 MiB free-memory tolerance
mistook WSL driver reservation for active GPU work. The prospective gate repair and unchanged
scientific inputs are documented in `PRE_RUN_GATE_NOTE.md` and Git history.

- Raw responses SHA-256: `42a3672c37c5587e2d6659c32aabf9d8b347642490f1594ec4c8a8edf0e016e3`
- Analysis file SHA-256: `6fcb9ee72feb5b83392dc1d708fe7fe403c4fba293da4f2582fbda031e43d8f1`
- Analysis content seal: `f8a58f1133717f24a3bb9abd5c3ceb1fa739f8a62441abdfa9ebc2d4b88749c0`
