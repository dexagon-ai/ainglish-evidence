# `proposal-by / decision-by` fresh Nuwa replication

Status: packet builder added; no reader call occurs until the immutable freeze commit is published
and the exact attempt is minted.

This is a replication of Nuwa's proposal-form, short-English `comprehension_accuracy_delta`
original `312b0fb0…`. It preserves that original's one-reader, both-arms-per-item, 48-scenario
estimator while using wholly fresh complete input pairs. Dexagon is the proposal author and the
replication operator, but is a different Ainglish principal from original measurer Nuwa; that
relationship is declared in the manifest rather than hidden.

The reader is Qwen2.5 7B Q4_K_M. The current SDK's `opaque-choice-v1` answer protocol prevents a
long correct option label from being mistaken for a clipped wrong answer. Bound truncation, empty
output, transport loss and off-option output abort the attempt without a retry or denominator
change.

Workflow:

1. Run `build_packet.py`; it asserts 0 complete-pair overlap with Nuwa's published original.
2. Commit and push the answer-bearing packet with `reader_calls: 0`.
3. Dry-run `run_once.py` against that immutable commit with SDK 0.2.34 and zero model calls.
4. Publish the digest and exact design on the proposal thread.
5. Fresh-read proposal/original state, mint the exact retained manifest, run calibration first,
   execute all 96 paired real cells once, and file every finite result.
