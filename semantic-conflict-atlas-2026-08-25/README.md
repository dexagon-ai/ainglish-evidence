# Semantic conflict and duplication atlas

Status: candidate builder and review-only classifier runner prepared. No model output has yet been
treated as a register relation. The final atlas will keep every row `review_required: true` and
`asserted_relation: null` even when both classifier families agree.

The classifier writes one fsynced review card per pair to `classifier-ledger.jsonl`; interrupted
review-only runs resume completed cards rather than silently losing hours of GPU routing work.
Set `AINGLISH_ATLAS_OLLAMA_URL` to bind the run to a dedicated, device-isolated Ollama service.
The supplied Modelfiles derive atlas-specific Gemma 3 12B and Mistral Small 3.2 24B readers from
the already digest-pinned local artifacts and replace their evidence-task system prompts.
After summarization, `verify.py` recomputes all three content pins, checks exact pair population and
order, validates the label enum, and refuses if any layer turns a review card into an asserted edge.
