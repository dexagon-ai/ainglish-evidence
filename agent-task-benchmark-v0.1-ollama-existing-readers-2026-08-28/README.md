# Existing-reader execution of the Ainglish agent-task benchmark v0.1

Status: **preregistered; inference results pending**

This directory binds the frozen
[`ainglish-agent-task-v0.1`](../end-to-end-agent-task-benchmark-v0.1-2026-08-28/README.md)
packet to a project-operated run over general-purpose model artifacts that were already installed on
Dexagon's local Ollama server on 2026-08-28. No model is downloaded by this run.

The primary question is deliberately narrow: for each reader and exposure track, does compact
Ainglish produce the same zero-repair task success as careful English that states the same source
intent explicitly? Bare English is a secondary ambiguity baseline. Cold and one-exposure results are
never pooled.

This is internal benchmark evidence. The operator and task designer are linked to Ainglish, model
training exposure is unknown, and distinct model tags are repeated readers rather than independent
human participants. A cold prompt is prompt-cold, not proof that the model never saw Ainglish during
training.

## Frozen execution

- [`RUN_PROTOCOL.md`](RUN_PROTOCOL.md) defines the estimands, exact inference contract, exclusion
  rules, interruption handling, and permissible claims.
- [`run_ollama.py`](run_ollama.py) discovers only the explicit allowlist, freezes the served artifacts,
  creates the common randomized prompt schedule, verifies checksums, and executes without pull calls
  or outcome-dependent retries.
- [`analyse.py`](analyse.py) applies the benchmark's exact scorer and reports paired reader-level
  Ainglish-versus-careful results, secondary bare comparisons, and construct-level diagnostics.
- `reader-roster.json`, `prompts.jsonl`, `RUN_PLAN.json`, and `SHA256SUMS.preregistered` are generated
  and committed before inference begins.
- Runtime records are written to `results/responses.jsonl`; every valid output, parser failure,
  transport failure, and interrupted in-flight cell remains in the denominator.

## Reproduction

The scripts use Python's standard library and a local Ollama HTTP API. Preparation fails if any
allowlisted tag is absent; it never asks Ollama to pull it.

```bash
python3 run_ollama.py prepare
python3 run_ollama.py verify
python3 run_ollama.py run
python3 analyse.py results/responses.jsonl
```

The exact server and artifact metadata are part of `reader-roster.json`. Reproducing the computation
does not establish independent replication: the tasks, protocol, and run remain project-linked.

