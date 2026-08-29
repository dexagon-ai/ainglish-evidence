# Frozen protocol

## Hypothesis

Larger exact-surface exposure should selectively improve cold operational use of the exposed
Ainglish constructs relative to both the untouched base and an equal-size adapter trained on the
same response task but on the other three constructs.

The experiment does not claim that supervised QLoRA equals future pretraining. It is an attainable
test of the weaker learnability premise behind the project's future-training rationale.

## Frozen populations

- Base: `Qwen/Qwen2.5-7B-Instruct` at revision
  `a09a35458c702b33eeacc393d103063234e8bc28`.
- Group A corpus: 600 rows each for list completeness, pronoun number, and claim source.
- Group B corpus: 600 rows each for role cardinality, recurrence, and failure contract.
- Evaluation: 48 held-out frames per construct under three isolated arms, 864 prompts total.
- Conditions: untouched base, adapter A, adapter B.

Every training and evaluation response is a shuffled opaque option label. Correct label positions are
balanced within each construct. Both training groups see identical system instructions and task
shape, but no exact message, identifier, action vocabulary set, or source row crosses between train
and evaluation.

## Training controls

- 4-bit NF4 with double quantisation and bfloat16 compute;
- LoRA rank 16, alpha 32, dropout 0.05 on attention and MLP projection modules;
- two epochs, per-device batch 4, gradient accumulation 4;
- AdamW, learning rate 2e-4, cosine schedule, 5% warmup;
- identical seed `2026083003` and one physical RTX 3090 per adapter;
- no checkpoints, resumes, hyperparameter searches, early stopping, or post-result retraining;
- offline-only model load and a 1 GiB ceiling per final adapter directory.

If a training process fails, its non-empty output is retained as an adverse execution artifact and
is not silently deleted or resumed.

## Evaluation and scoring

Each condition gets the exact same frozen prompt order, greedy decoding, maximum 16 new tokens, and
strict one-key JSON parser. There are no inference retries. An interruption or malformed output is
an incorrect cell and remains in the denominator.

For each construct, `exposed` is its assigned adapter and `unexposed` is the cross-over adapter.
Primary cold contrasts are exposed-minus-base and exposed-minus-unexposed. Careful-English and bare
arms are safety diagnostics.

Prospective per-construct interpretation:

- `selective_uptake` requires exposed cold accuracy at least 0.80, gains of at least 0.10 over both
  base and unexposed, careful-English degradation versus base no worse than 0.05, and bare ambiguity
  degradation no worse than 0.05;
- `broad_behavior_shift` applies when both adapters change cold accuracy from base in the same
  direction by at least 0.10 and are within 0.05 of one another, or when exposed careful/bare
  performance degrades by more than 0.10;
- otherwise `no_demonstrated_selective_uptake`.

The report also gives group-aggregate results and every cell. Favourable, null, adverse, malformed,
and interrupted outcomes are all published.

## Claim boundary

The model, corpora, harness, and operator are project-linked. Results are not human validation,
independent evidence, an Ainglish measurement, a settlement voice, or a ballot recommendation.
Current English advantages and current tokenizer costs remain real observations; future Ainglish
training benefits remain prospective beyond this narrow supervised experiment.
