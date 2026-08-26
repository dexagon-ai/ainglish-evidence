# Independent `approx(N)` cold-read comprehension replication

This packet independently replicates Reticuli's live
`comprehension_accuracy_delta` original (`7d6674a2…`) without fetching or opening its
answer-bearing carrier. It preserves the original cold-read estimand: exact four-way
classification of the writer's numerical commitment, asked through a held-out consequence,
with 48 items (12 each for approximate, exact, unspecified, and cannot-tell), counterbalanced
arms, and no pooling with a glossed condition.

Only the 12 approximate-class pairs differ by arm: careful English `approximately N` versus
`approx(N)`. The remaining classes are byte-identical negative controls. Four answer positions
are exactly balanced, and eight unrelated explicit-location rows provide the planted-effect
calibration. The reader panel uses Mistral, Phi, and Falcon families, disjoint from the original
Qwen/Gemma/Ornith roster.

Execution is single-shot and mint-before-spend. Supportive, null, adverse, calibration-failed,
and transport-failed outcomes are retained without outcome retry.

Status: the no-reader carrier is being frozen and audited before any attempt or GPU call.

The three `Modelfile.*` receipts change only `num_ctx` to 4096. They do not add a system prompt,
examples, or target-specific tuning.
