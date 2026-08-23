# Construct-blind reader qualification tournament

This one-shot development screen freezes 32 ordinary-English controls across four semantic
axes before any new proposal evidence is read. It is instrument qualification, never evidence
for an Ainglish proposal.

The selection rule is in `spec.json`: a reader must emit an exact fixed option for every cell,
score at least 30/32 overall and at least 7/8 on every axis. All qualifying, distinct model
lineages form the fixed roster. The isolated reader store contains the two generic literal-reader
instruments used here (Mistral and Gemma); the task-specific event models and the shared-server
Qwen model are deliberately outside the candidate set. Fewer than two qualifying lineages stops all planned
comprehension work; deterministic token work may continue.

Run only against the dedicated GPU-0 Ollama endpoint on port 11435, with no resident model on
either the shared or dedicated endpoint at preflight. The script is deliberately one-shot and
will not overwrite `result.json`.
