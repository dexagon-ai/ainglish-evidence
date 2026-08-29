# Controlled cross-over training-exposure study v1

Status: **protocol preparation; no training or evaluation yet**

This no-download development study tests whether substantially larger, construct-specific supervised
exposure changes operational use of six current Ainglish candidates. It improves on the earlier
76-row pilot by using two equal-size cross-over adapters:

- adapter A: list completeness, pronoun number, and claim source;
- adapter B: role cardinality, event-versus-state recurrence, and failure contract.

Each adapter receives 600 unique Ainglish consequence examples per assigned construct, 1,800 rows
total. Both corpora use the same task grammar, label balancing, optimiser, base revision, seed,
quantisation, row count, and training schedule. For any one construct, the other adapter is therefore
an unexposed task-format control rather than an untrained model with a different interaction style.

Evaluation is frozen before training: 48 new frames per construct across cold Ainglish, full careful
English, and deliberately underspecified bare English. Training and evaluation vocabularies,
identifiers, messages, and rows are disjoint. The complete plan is 864 prompts per model condition
and 2,592 predictions across base, adapter A, and adapter B.

This is a supervised QLoRA development experiment, not a simulation of foundation-model pretraining.
It can show whether the exact forms are learnable under controlled exposure; it cannot prove future
tokenizer efficiency, human comprehension, independent governance evidence, or ratification.

## Two-stage freeze

```bash
python3 build.py
python3 audit.py
# Commit and push the complete corpora, evaluation, code, and checksums.

CUDA_VISIBLE_DEVICES=0 /home/dexagon/.venvs/ainglish-train/bin/python train.py --group a
CUDA_VISIBLE_DEVICES=1 /home/dexagon/.venvs/ainglish-train/bin/python train.py --group b

python3 freeze_artifacts.py
# Commit and push adapter-receipts.json before evaluation.

CUDA_VISIBLE_DEVICES=0 /home/dexagon/.venvs/ainglish-train/bin/python evaluate.py --condition base
CUDA_VISIBLE_DEVICES=1 /home/dexagon/.venvs/ainglish-train/bin/python evaluate.py --condition adapter-a
# Run adapter-b after either GPU is free.
python3 analyse.py
```

All model loads are `local_files_only=True` under offline environment flags. Training saves final
LoRA adapters only—no optimiser checkpoints—and each artifact has a hard 1 GiB size ceiling.
