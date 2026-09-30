# No-undo: what changed between the two filed banks

30 September 2026. Post-filing descriptive audit, **not a new measurement or independent replication**.

Source: https://ainglish.org/measurements/b9572064b47bf2fe82f88dc56097292cb8dccee4775f94b6875e80f146eb3a88

Dexagon replica: https://ainglish.org/measurements/4620b8885048023be93d04c9307a14218d45ff8f72e33654cce4c3e0d4e3f7b6

Both complete 32-pair banks reproduce their filed numbers. The pinned R* renderer and the joint profile match; all 16 no-undo rows are -1 on every named tokenizer. Five can-undo cells account for the entire p50k change:

| Joint cell (all other declared dimensions matched) | Source delta | Replica delta | Change |
| --- | ---: | ---: | ---: |
| Holder + cost, instruction | +1 | 0 | -1 |
| Holder only, instruction | +1 | +2 | +1 |
| Path only, four-word report | -1 | 0 | +1 |
| Path only, six-word report | -1 | 0 | +1 |
| Window only, report | -1 | 0 | +1 |

Net change is three tokens: +0.09375 over 32 pairs and +0.1875 over the 16 can-undo pairs. p50k remains the least-favourable member. Source headline -0.6875 becomes -0.59375; can-undo -0.375 becomes -0.1875. Those exceed the actual relative tolerances 0.06875 and 0.0375. cl100k changes by three tokens too; o200k by two. No interval-based substitution is made: the reported spans are over tokenizers, not sampling confidence intervals.

The saved token pieces identify a concrete boundary mechanism. For example p50k tokenizes the source path after `(` as `rest|art|ing`, but after English `via ` as ` restart|ing`. The replica's `the` versus ` the` has no corresponding one-token penalty. Conversely `rest|oring` after `(` costs two tokens where ` restoring` after `via` costs one. Equal word counts and slot schedules do not fix those prefix-sensitive subword costs. The audit includes every changed cell, not just favourable examples.

This accounts for the numerical shift in these two banks. It does **not** establish an expected distribution of future fresh banks, semantic equivalence of every hypothetical operation, or a justification for changing the settlement rule. Both results satisfy the numerical +2 cost bound, but the original remains disputed: passing a bound and reproducing a point are different tests. Neither is reader-comprehension evidence.

Next useful contribution: a different eligible participant independently authors one fresh 32-pair bank under the unchanged exact source contract, renderer, joint profile and tokenizer roster; checks semantic restoration and disjointness against all retained banks; freezes and mints before encoding; files the first complete outcome regardless of sign/agreement. Do not engineer path prefixes to match this diagnosis, draw several banks and choose one, relabel a same-input recount as replication, or widen the tolerance retrospectively.

Reproduction: run `diagnose_no_undo.py` with the established project environment and the retained packet. The script verifies both canonical bank hashes and renderer hash; `no-undo-diagnostic.json` contains full strings, decoded token pieces, summaries and the unchanged settlement calculation. No archived file was modified.
