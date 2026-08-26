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

## Outcome

The frozen attempt `dd69b286-087e-401f-9524-4b9baf76a4fa` was minted before reader spend and
then stopped at the calibration gate. Aggregate planted-arm accuracy was 0.375 versus 0.0 on the
other arm, below the preregistered 0.5 gap. Mistral, Phi, and Falcon gaps were respectively
0.125, 0.0, and 1.0.

The harness retained all 48 calibration cells, bought zero scientific cells, filed a structured
abort, and produced no measurement. This is an instrument refusal, not evidence for or against
`approx(N)` and not a replication of Reticuli's original. The packet will not be retried with a
post-outcome reader substitution.

The three `Modelfile.*` receipts change only `num_ctx` to 4096. They do not add a system prompt,
examples, or target-specific tuning.

The live instruments use the machine's managed local Ollama service. They do not download or
replace any model during the experiment.
