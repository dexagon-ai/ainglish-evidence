# Reader qualification v6: new-lineage laboratory

## Pre-inference abort

V6 was permanently aborted before any model call or qualification-item exposure. Its frozen
transport requested `think: false` and required zero returned thinking bytes, but current official
Ollama documentation states that GPT-OSS instead requires a `low`, `medium`, or `high` thinking
level and cannot fully disable its trace. One partial source-model transfer was stopped; no v6
download completed and no source model or wrapper was installed. `preflight-abort.json` seals the
observed state and reason. Never run this plan; use its separately frozen successor.

This is a fresh, one-shot, construct-blind qualification screen for five model lineages that have
never appeared in this evidence repository. It uses only ordinary English and never counts as
evidence for an Ainglish proposal. No v5 reader is repeated, no burned qualification item is reused,
and no prompt, threshold, transport bound, or answer key may be tuned after a candidate sees an item.

The 64-item plan is frozen before any candidate download or inference. Eight semantic axes receive
eight items each. A reader qualifies only with 64/64 exact opaque choice codes, at least 60/64
correct, at least 7/8 correct on every axis, and zero returned hidden-thinking bytes. A scientific
roster is ready only when at least two distinct lineages qualify.

Candidate order is fixed in `plan.json`:

1. Phase A: OpenAI GPT-OSS 20B MXFP4 and LG AI Research EXAONE 3.5 32B Q4_K_M.
2. Reserve B, only if the accumulated roster is not ready: Ai2 OLMo 2 13B Q4_K_M and TII Falcon 3
   10B Q4_K_M.
3. Final reserve, only if the accumulated roster is still not ready: THUDM GLM-4 9B Q4_0.

The published Ollama registry manifest digest and underlying model-blob digest are frozen for every
candidate. Pulling a tag that has moved is a refusal, not an implicit model substitution. Each
tracked Modelfile adds the same literal-reading system instruction, temperature zero, and a 4,096
token context. The resulting wrapper digest is pinned in the phase holdout before its first call.

Run order:

```text
python3 build_plan.py
# commit and push plan.json before ollama pull

ollama pull gpt-oss:20b
ollama pull exaone3.5:32b
ollama create dexagon-gpt-oss-20b-qualification-v6:ctx4k -f Modelfile.gpt-oss
ollama create dexagon-exaone3.5-32b-qualification-v6:ctx4k -f Modelfile.exaone
python3 build_phase.py --phase phase-a
# commit and push phase-a-holdout.json before inference
python3 run_once.py --phase phase-a
```

Later tranches follow only when the accumulated published results still contain fewer than two
qualified lineages. Every null, malformed, adverse, fault, and supportive outcome is retained. A
failed reader cell is never repeated. Scientific proxy, evidential-tag, modal/operational, and
ratified-census campaigns remain barred until `selected-result.json` says `roster_ready: true`.

Primary model references:

- https://ollama.com/library/gpt-oss:20b
- https://ollama.com/library/exaone3.5:32b
- https://ollama.com/library/olmo2:13b
- https://ollama.com/library/falcon3:10b
- https://ollama.com/library/glm4:9b
