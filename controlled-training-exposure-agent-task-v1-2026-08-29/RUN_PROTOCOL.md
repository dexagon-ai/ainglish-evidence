# Frozen run protocol

## Question and estimands

The narrow causal intervention is attachment of one frozen LoRA adapter to one frozen base model.
All other declared inference factors are fixed.

For each exposure class and prompt track, the primary descriptive contrasts are:

1. adapter minus base zero-repair task success on the Ainglish arm;
2. adapter minus base final task success on the Ainglish arm; and
3. within each model condition, Ainglish minus careful-English task success.

Adapter-minus-base contrasts on careful and bare English are negative-control diagnostics for broad
behaviour change. Cold and one-exposure tracks are never pooled. The one-exposure reference cost is
included in its prompt tokens. A cold prompt is prompt-cold; it is not evidence about unknown base
pretraining data.

## Population and exposure boundary

The complete frozen v0.1 benchmark has 22 items, three surface arms, and two tracks, producing 132
cells per model condition and 264 planned observations. The exact schedule is shared across the base
and adapter conditions.

Exposure classes are assigned using the development adapter's preregistered corpus manifest. Exact
markers for four transfer-holdout constructs were excluded from all development training rows,
including cross-reference rows. The other seven benchmark constructs are `trained_surface`.
Withheld-surface results are a transfer diagnostic, not proof that the adapter never encountered the
meaning or ordinary-English wording.

## Fixed inference contract

- Base: `Qwen/Qwen2.5-7B-Instruct`, revision
  `a09a35458c702b33eeacc393d103063234e8bc28`.
- Adapter: the local artifact pinned by
  `../ainglish-learning-program-2026-08-25/adapter-artifact-receipt.json`.
- Tokenizer: the pinned base tokenizer for both conditions.
- Quantization: bitsandbytes NF4 4-bit, double quantization, bfloat16 compute.
- Decoding: greedy, `do_sample=False`, at most 96 new tokens, seed `2026082901`.
- Scheduling: fixed seed `2026082902`; base and adapter receive identical cell order.
- Fresh conversation for every cell; sequential execution within each condition.
- Strict JSON parser and exact action schema from the benchmark.

The complete generated continuation is retained. Markdown fences, prose, extra keys, unknown action
IDs, empty outputs, and refusals are invalid. If the first response is a valid clarification, the
frozen sender clarification is appended to the same conversation and one repair response is
requested. A repair must be an exact valid action object.

## Failure, interruption, and retry policy

There are no inference retries or outcome-dependent prompt changes. Before every generation the
runner writes an atomic in-flight receipt. If restarted after interruption, the interrupted call is
materialized as an invalid observation and execution continues; completed cells are never repeated.
Model-load failure stops the condition without inventing observations.

## Analysis and claim limits

Every planned cell remains in the denominator. Paired contrasts report adapter-only successes,
base-only successes, and ties. Tokens are secondary and reported separately for all calls and for
pairs where both conditions reached the same declared success stratum. Latency is descriptive local
hardware performance only.

The study may show that this adapter changes this model's behaviour on these frozen tasks. It cannot
establish human intuitiveness, independent replication, external adoption, future tokenizer
efficiency, general model-family benefit, or eligibility for proposal ratification.
