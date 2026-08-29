# Agent-task benchmark post-hoc audit v1

This package performs a deterministic, inference-free robustness audit of the completed
`agent-task-benchmark-v0.1-ollama-existing-readers-2026-08-28` result. It does not alter the frozen
benchmark, rerun any reader, or turn an exploratory analysis into preregistered evidence.

## Questions

1. Does giving each declared model lineage equal weight materially change the reader-weighted result?
2. Does the direction survive leaving out any one lineage?
3. How much does one prompt-local definition change the Ainglish comparison?
4. Is the result driven by the two readers with known operational pathologies?
5. Which frozen constructs account for the largest positive and negative differences?

The manual lineage map treats all Qwen versions as one lineage and every other installed family as
one lineage. This reduces obvious pseudo-replication from the six Qwen artifacts, but it does not
prove that the remaining lineages are statistically independent. The roster was one of convenience,
not a random sample from a model population.

## Run

From this directory:

```bash
python3 analyse.py
```

The standard-library-only script verifies the frozen source hashes, then rewrites `AUDIT.json` and
`AUDIT.md` deterministically. It makes no network, model, or GPU calls.

## Interpretation boundary

The equal-lineage bootstrap interval, sign probability, sensitivity exclusions, construct ranking,
and leave-one-lineage-out calculations are exploratory descriptive diagnostics. They are not a new
governance measurement, independent replication, human-intuitiveness study, or population-level
confidence statement. In particular, the 2,904 cells are not treated as 2,904 independent samples.

`solar-pro:22b` remains in the main analysis despite returning HTTP 500 for every cell, and
`deepseek-v2:16b` remains despite 127/132 schema-invalid first outputs. Their joint exclusion is a
clearly labelled post-hoc sensitivity calculation only.
