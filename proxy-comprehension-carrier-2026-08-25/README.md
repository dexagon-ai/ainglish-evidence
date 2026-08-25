# `proxy(<M>)` comprehension carrier

This is a frozen 96-scenario, four-arm carrier for the measured `proxy(<M>)` proposal. Each
scenario states a claimed construct `X` and a distinct measured quantity `M`. The arms are:

1. `X proxy(<M>)`;
2. the complete careful-English disclosure;
3. bare `X, and I measured M`;
4. source-only `X obs(M)`.

Every item asks both registered held-out questions jointly: whether `M` is identical to `X`, and
whether the bridge from `M` to `X` has been verified. Question polarity rotates through four
frames, so a reader cannot succeed by returning one fixed yes/no code. Domains, lexical frames,
and opaque-option positions are balanced. `build_items.py` performs no model, network, tokenizer,
or governance call.

The complete-English arm is the confirmatory comparator for the non-inferiority claim. Bare and
`obs` arms are descriptive distinctiveness diagnostics and must not replace that comparator.
The public item commitment precedes all reader calls. A run remains gated on a qualifying roster
with at least two genuinely distinct model lineages.
