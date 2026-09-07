# Mistral contextual transfer: completion readback

Status: stopped_without_final_result.

323 completed model calls; 0 uncertain calls retained. The finisher made zero inference calls.

The run uses the original pinned CPU-only Mistral reader and fixed settings. The continuation reuses only exact completed responses locally and spends only previously unstarted calls. This is one interrupted-and-continued study, not a new independent replication.


## Boundaries

- This is a same-author readback/reproducibility audit, not an independent replication.
- Original CPU reader, options, controls, inputs and gates are unchanged; completed calls were not repeated.
- Counts describe three authored contexts, not broad operational efficacy or future Ainglish-trained performance.
- Ollama token counts are observed counters, not token IDs or provider billing.
- No final result exists. Only completion/uncertainty counts are reported; no partial target-accuracy headline is selected. The finisher does not infer the stopping cause or retry an uncertain call.
