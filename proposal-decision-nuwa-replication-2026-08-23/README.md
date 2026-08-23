# `proposal-by / decision-by` fresh Nuwa replication

Status: **stopped at calibration; no scientific row read and no measurement filed**.

The first retained attempt (`2ad8d17c…`) stopped at its preregistered calibration gate after 12
calls and before every scientific row. Its calibration wrongly used the unfamiliar construct as
the planted cue, so failure could not distinguish reader/parser incompetence from the very
construct incomprehension under study. The attempt was typed-aborted without retry. The frozen v2
packet replaces only those six rows with construct-free explicit-prose controls and discloses the
predecessor; all 48 untouched scientific pairs remain unchanged and unread.

The v2 successor (`8cb3fd98…`) also refused before scientific spend: its construct-free explicit
arm exceeded the opaque arm by 0.3333, below the frozen 0.5 calibration floor. That attempt was
typed-aborted after 12 calls without retry. This reader/instrument line is closed rather than
lowering or repeatedly redesigning the positive control until it passes. The two refusals are not
semantic evidence for or against `proposal-by`; they establish that this Qwen2.5-7B Q4_K_M panel
did not qualify to estimate the registered delta.

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
