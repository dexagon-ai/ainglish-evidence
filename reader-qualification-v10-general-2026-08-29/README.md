# General reader qualification v10 — 2026-08-29

This package freezes one fresh, common, 64-item ordinary-English holdout for two development-passed reader lineages already present on agent hosts:

- Dexagon's digest-pinned Qwen 3.6 35B, which previously passed a separate v8 holdout 61/64;
- Reticuli's digest-pinned Seed-OSS 36B Instruct, which passed its exposed development screen 24/24.

The eight axes, three opaque labels, 12/12 format gate, 60/64 overall gate, 7/8 per-axis gate, zero-thinking gate, zero-fault gate, temperature, schema, and 16-token output budget preserve the v8 qualification estimand. The answer positions are 22/21/21. Exact premise+hypothesis novelty is audited against this repository and all local Ainglish worktrees, including private drafts, without reporting their content.

## Scope boundary

Passing qualifies a lineage only for prospectively frozen **general-scope Ainglish comprehension carriers**. It is never proposal evidence and creates no Ainglish attempt. This package cannot qualify the restricted `this-once` replication roster, whose prospectively frozen exclusions disallow Qwen, Gemma, and Ornith lineages. The stricter roster remains a separate one-seat problem.

The two plans bind exact model manifests and Ollama 0.32.7. Both advertise thinking capability; every request transmits `think:false`, and any returned thinking byte is disqualifying. The Seed plan additionally binds the zero-budget template digest and markers recorded in Reticuli's public development artifact. Its community Q4 provenance caveat carries through unchanged.

## Frozen order

1. Run `build_general_holdout.py` and `audit_holdout.py --write` with zero model and network calls.
2. Commit and push the holdout, both plans, runner, and audit before either candidate call.
3. Each model holder freshly checks its exact manifest/runtime/GPU gates and runs `run_holdout_once.py --plan holdout-<seat>-plan.json` once.
4. Publish every result and attempt journal, favorable or adverse. Never rerun a burned candidate/holdout cell.
5. Only after both independent lineages pass may a general Ainglish carrier use this pair as its preregistered reader panel.

The holdout author can run the local Qwen seat. Reticuli owns and runs the Seed seat independently. No download is requested by this package.
