# Controlled training-exposure agent-task study v1

Status: **protocol preparation; no inference results yet**

This development study asks whether the existing Ainglish QLoRA adapter changes task execution on
the frozen [`ainglish-agent-task-v0.1`](../end-to-end-agent-task-benchmark-v0.1-2026-08-28/README.md)
battery. It compares the same pinned Qwen 2.5 7B base artifact with and without the already-frozen
adapter. The tokenizer, quantization, prompts, order, decoding, hardware class, parser, and repair
policy are held fixed. No model is downloaded.

The benchmark's 11 constructs are prospectively split by the adapter corpus boundary:

- `trained_surface`: the development corpus contains the construct's registered surface;
- `withheld_surface`: the corpus builder excluded the construct and every row containing either of
  its exact registered markers.

The labels describe controlled exposure to exact Ainglish surfaces, not absence of related English
concepts from pretraining. The adapter and study operator are project-linked. Results are product
research, never independent Ainglish governance evidence.

The co-primary outcomes are zero-repair and final task success. Invalid output, wrong action,
clarification, repair failure, tokens, and latency remain separate. Token deltas are interpreted only
within explicitly reported correctness strata; no composite score lets shorter failures beat correct
answers.

## Reproduction

Preparation creates the frozen cells, exposure map, plan, and checksums. The runner refuses to start
until those files are committed and reachable from public `origin/main`.

```bash
python3 build.py
python3 run.py verify
/home/dexagon/.venvs/ainglish-train/bin/python run.py run --device-index 1
python3 analyse.py results/responses.jsonl
```

`run.py` uses `local_files_only=True` for both the base model and adapter. It never calls a model hub
or Ollama pull endpoint. Each cell starts a fresh conversation; only a valid first-turn clarification
receives the benchmark's frozen repair message. There are no inference retries.
