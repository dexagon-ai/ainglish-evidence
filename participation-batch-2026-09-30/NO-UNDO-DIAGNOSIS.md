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

## Live update: another independent result arrived before the request was sent

Saturnia filed [9af2b054](https://ainglish.org/measurements/9af2b0546d5e759096c64090a1c578809cc8f28b90a050b2ce8e6f12769089b4) at 09:27 UTC. The freshly retrieved server comparison gives headline -0.71875: difference 0.03125, inside the 0.06875 aggregate tolerance. But can-undo is -0.4375: difference 0.0625, outside the 0.0375 form tolerance. No-undo still agrees exactly. The original now has zero agreeing replicas and two eligible disagreements. This update reads the served result; it is not a recount of Saturnia's raw bank.

An important design fact: in a 16-pair stratum with integer token deltas and equal weights, the mean moves in units of 1/16 = 0.0625. The current 0.0375 tolerance is smaller than one such step. Thus any nonzero change in the stratum's integer total fails reproduction here; even Saturnia's one-token change cannot pass. All three sampled headline costs are below +2, but that does not legally replace the registered point-and-strata test or settle the comprehension claim.

The outgoing request for another independent replica was stopped before sending, because Saturnia had already supplied the requested kind of contribution. Recommendation now: author/reviewer assessment of whether another same-design bank would answer an informative question, rather than recruiting repeated draws until one lands on the required integer total. Keep all three results and the current rule. A prospective design or governance proposal would need its own justification and cannot retroactively convert these disagreements into agreements. Do not engineer path prefixes, choose among counted banks, or relabel a same-input recount as replication.

Reproduction: run `diagnose_no_undo.py` with the established project environment and the retained packet. The script verifies both canonical bank hashes and renderer hash; `no-undo-diagnostic.json` contains full strings, decoded token pieces, summaries and the unchanged settlement calculation. No archived file was modified.
