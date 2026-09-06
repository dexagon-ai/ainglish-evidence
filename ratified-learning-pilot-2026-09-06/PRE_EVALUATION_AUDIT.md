# Additional audit before target evaluation

6 September 2026. The first adapter is trained; the matched-English adapter is training.
No target evaluation has run. Frozen training/evaluation/scoring are unchanged.

The exact source mappings still match the live 0.51.0 register (all six checked through the SDK).
Five executable design/export tests pass. Train-only ZIP membership is allowlisted and deterministic.

Important limitation found in the input audit: option letters rotate, but **are not balanced**.
Training answers are A=72, B=39, C=33. Test answers are A=26, B=22, C=48, across 96 cases.
The majority-label test baseline is therefore **50%, not one third**. A training-set majority-A
shortcut would score 26/96 (27.08%) on this deliberately shifted test. Report the distribution and
per-label accuracy with any result; do not describe label rotation as balancing.

This does not change which answer is correct or the paired language comparison: every weight and
prompt condition receives the same options and gold. It does limit an absolute headline and leaves
positional/task-pattern sensitivity open. Keep this pilot descriptive; a later independent benchmark
should balance answer locations explicitly and use a broader set of semantic frames.

The twelve topic/family clusters are mechanically expanded, not twelve independent natural work
environments. The sixteen rows per construct reuse eight semantic patterns twice. Boundary flags are
the predetermined variants 3/6/7, not an exhaustive safety suite. The two-turn worked examples are
teaching material only; the 144-row adapter training files use single-question consequence tasks.

No evaluation data is modified, no outcome is selected, and no claim of general model improvement is
licensed by a favourable number. Preserve this note next to the eventual results.
