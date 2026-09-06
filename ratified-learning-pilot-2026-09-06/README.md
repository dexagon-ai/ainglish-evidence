# Ratified language: controlled learning pilot

Status: design, curriculum and analysis frozen before model calls.

Question: on six human-readable ratified distinctions, does controlled Ainglish exposure help a
cached Qwen2.5-7B-Instruct model apply the meanings to held-out tasks, beyond what the same tasks
and answer format taught in careful English achieve? A short reference is a separate condition.

This is synthetic development research, not an independent comprehension panel, natural adoption,
foundation-model pretraining experiment, tokenizer adaptation or governance evidence.

## Design

- Source: six full mappings in immutable `ainglish-core-v3`, with source and construct digests.
- 144 meaning-matched training pairs, six teaching cards, plus worked two-turn teaching dialogues.
- 96 held-out cases, four prompt arms and three weight conditions: 1,152 planned target responses.
- Training/evaluation have different full prompts, topic names and framing. Semantic case patterns
  are shared: this is transfer to held-out framings, **not** transfer to unseen concepts or a large
  independent sample. There are 12 held-out topic/family clusters; report all six families.
- Untouched base versus two independently initialized LoRAs: Ainglish training and careful-English
  training. Same model revision, quantization, seed, rows, answers, optimizer and epoch schedule.
  Input lengths differ; token exposure and timing are reported, not called equal compute.
- Cold Ainglish, short-reference Ainglish, cold careful English, short-reference careful English.
  The reference has the same semantic scope in both renderings; count its tokens.
- Closed multiple-choice consequential interpretation, not a real tool action. Token costs are
  **one-turn reading costs**, not observed savings across a completed workflow. No repair loop.
- Twelve target-independent format controls per weight condition precede target evaluation; fewer
  than 10/12 correct aborts that condition. This is a research instrument check, not a registered
  reader qualification or proof of independent reader lineages.
- No retry on inference/transport failure; each batch gets an in-flight receipt first. An interrupted
  batch is a failed run, not silently retried. Raw outputs, failures and all denominators remain.

Primary report: the paired cold-Ainglish accuracy difference between the two trained conditions,
alongside their cold-English difference and difference-in-differences. A positive difference alone
does not establish selective learning if English or boundary-case accuracy loses more than 5 pp.
Report base/reference comparisons and per-family results even if adverse. Cluster bootstrap intervals
are exploratory (12 synthetic clusters); one seed/model cannot establish general benefit.

## Data use

`curriculum.jsonl`, `train-ainglish.jsonl`, `train-english.jsonl`, `guides.json`, `TEACHING.md`,
`conversations.jsonl` and `source-constructs.json` are non-normative teaching material under CC0-1.0.
They are agent-authored synthetic examples, manually reasoned about by their author and checked by
executable structural/semantic guards; **no independent or human review is claimed**. They do not
amend the ratified register and are not an official project release or an update to v3.

`evaluation.jsonl` and subsequent raw results are separate evaluation/research artifacts. Do not put
them into a train-only export or call them fresh holdouts after publication. Do not mirror this whole
research folder as a training dataset. `export_training.py` creates a digest-labelled train-only ZIP
from an explicit allowlist and cannot include evaluations or result journals.

New language examples in this folder are dedicated under CC0 1.0 Universal; the instrument code
is MIT (see `LICENSE-MIT.txt`). Source language retains its release notice. This limited dedication
does not relabel unrelated evidence, contributor identities, private messages or other repository files.

## Reproduce without downloading a model

Requires the already cached Qwen revision `a09a35458c702b33eeacc393d103063234e8bc28` and an existing
training environment with torch, transformers, peft and bitsandbytes. The runner forces offline mode,
uses one explicitly selected GPU and refuses an existing result/artifact rather than overwriting it.
Saves only final LoRAs, at most 512 MiB each; no optimizer checkpoints or full-model copies.

1. `python build.py`; `python -m unittest discover -s . -p 'test_*.py'`; `python audit.py --freeze`.
2. Commit and push the frozen inputs/code/checksums before training.
3. `CUDA_VISIBLE_DEVICES=0 /home/dexagon/.venvs/ainglish-train/bin/python run.py train ainglish`
   and then the same command with `english`. Both are trained before target evaluation.
4. `python run.py seal` then commit/push `adapter-receipts.json` before evaluation.
5. Run `run.py evaluate base`, `evaluate ainglish`, `evaluate english` in the same isolated/offline
   environment. Base and trained readers share a lineage; this is intentionally a within-model study.
6. `python analyse.py`; publish complete outputs and limitations. Do not tune after looking at them.

The published freeze is the preregistration for this development exercise, not an Ainglish attempt.
No GPU call, vote, measurement or proposal-state change is authorized by a favorable pilot result.
