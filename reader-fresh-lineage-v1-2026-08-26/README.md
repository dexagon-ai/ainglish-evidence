# Fresh reader-lineage search v1

The qualification repository already contains substantive screens from 18 named model lineages,
including Gemma, Mistral, several Qwen editions, Llama 3.1 8B, Command R7B, Phi-4, Granite,
EXAONE, InternLM, DeepSeek, OLMo, Falcon, and GLM. More small editions from the same families are
unlikely to solve the observed `not determined` weakness or provide convincing panel diversity.

`research.json` ranks six feasible larger candidates from official Ollama artifacts. The primary
pair is Llama 3.3 70B Q4_K_M and Solar Pro 22B. Llama 3.3 is the strongest model that should fit
sequentially across the two 3090s, though it remains correlated with the tested Llama family. Solar
Pro provides the more valuable independence seat: a previously untested Upstage architecture and
producer. Command R 35B, Aya Expanse 32B, Yi 34B, and Nemotron 70B remain ordered reserves with
their correlation or capability caveats recorded.

Acquisition is not inference. After the selected models download, their exact registry manifests
and local `/api/show` capabilities must be frozen. Any `thinking` capability or fit failure aborts
that candidate before semantic exposure. Each compatible candidate must next pass the independent
structured-format gate before seeing the exposed 24-item semantic development packet.

Primary references:

- https://ollama.com/library/llama3.3/tags
- https://ollama.com/library/solar-pro
- https://docs.ollama.com/capabilities/structured-outputs

The generic staged runner is committed independently of any candidate plan. After acquisition,
`build_candidate_plan.py` pins the local manifest and capabilities. `run_candidate_once.py` first
runs the 12 format-only controls; a strict failure publishes without exposing a semantic item. A
passing candidate then sees the already-exposed balanced 24-item development packet through JSON
schema output. Its prospective semantic gate is 22/24 overall, at least 2/3 per axis, at least 7/8
per label, exact schema on every cell, and zero thinking or fault cells. Passing means only that a
fresh v8 holdout may be worth authoring.

`audit_candidate.py` derives parsing, schema, answer, and aggregate projections again from each
raw response and binds the result rows to the durable attempt-journal sequence. Run
`python3 -m unittest -v reader-fresh-lineage-v1-2026-08-26/test_candidate_harness.py` from the
repository root for adversarial coverage of invalid/empty answer codes, raw projection drift, and
journal/result divergence.

## Solar Pro outcome

The exact Solar Pro 22B candidate plan was committed and published before its first call. All 12
format-stage requests returned HTTP 500 with no answer body, so the strict format gate failed and
the runner exposed zero semantic-development items. This is a terminal retained transport failure
for that plan: the cells are not retried, Solar does not enter a holdout, and the result is not
reader-qualification or proposal evidence. The next already-selected candidate is Llama 3.3 70B.
