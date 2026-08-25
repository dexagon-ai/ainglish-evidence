# Reader qualification v7: no-thinking new-lineage laboratory

V7 supersedes the permanently aborted v6 plan. V6 exposed no qualification item and made no model
call, so this plan carries its exact sealed 64-item packet forward without modification. It excludes
GPT-OSS because that family cannot disable its reasoning trace under Ollama's current API.

Every v7 candidate must pass two compatibility checks before seeing an item: its official Ollama
library entry must not advertise the `thinking` capability when this plan is frozen, and its local
`/api/show` response after the pinned source is acquired must not contain `thinking` in the
capability list. A mismatch is a pre-inference refusal, not a transport change.

The screen uses only ordinary English and never counts as evidence for an Ainglish proposal. Eight
semantic axes receive eight items each. A reader qualifies only with 64/64 exact opaque choice
codes, at least 60/64 correct, at least 7/8 correct on every axis, zero returned thinking bytes, and
zero fault cells. A scientific roster is ready only when at least two distinct lineages qualify.

Candidate order is fixed in `plan.json`:

1. Phase A: LG AI Research EXAONE 3.5 32B and Shanghai AI Laboratory InternLM 2 20B.
2. Reserve B, only if needed: DeepSeek V2 Lite 16B and Ai2 OLMo 2 13B.
3. Final reserve, only if needed: TII Falcon 3 10B and THUDM GLM-4 9B.

Published Ollama registry manifest and model-blob digests are frozen for every candidate. Each
tracked Modelfile adds the same literal-reading instruction, temperature zero, and 4,096-token
context. The wrapper digest and source capability response are pinned in the phase holdout before
the first candidate call. Every attempt is durably journalled before its request; no cell is ever
repeated.

Primary model references:

- https://ollama.com/library/exaone3.5:32b
- https://ollama.com/library/internlm2:20b
- https://ollama.com/library/deepseek-v2:16b
- https://ollama.com/library/olmo2:13b
- https://ollama.com/library/falcon3:10b
- https://ollama.com/library/glm4:9b
