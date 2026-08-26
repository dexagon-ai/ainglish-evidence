# Next reader-candidate audit

This is the no-download decision record for the reader-qualification lane after v8. It makes no
model calls and does not expose a new holdout.

## Decision

There is no eligible unused model lineage in the local Ollama inventory.

- Qwen 3.6 35B is the sole v8-qualified reader, so additional Qwen editions cannot supply the
  required independent base lineage.
- Gemma, Llama, Granite, Command R, Phi, EXAONE, InternLM, DeepSeek, OLMo, Falcon, GLM and Mistral
  have already consumed and failed a frozen development or qualification gate. A failed cell is not
  rerun under a new wrapper.
- Ornith-1.0-35B is Qwen-3.5-derived and therefore cannot supply a new base lineage.
- GPT-OSS 20B is a distinct base lineage but is ineligible under the unchanged instrument: the v6
  preflight established that its official Ollama transport requires a `low`, `medium`, or `high`
  reasoning level and cannot guarantee zero returned thinking bytes. No qualification item was
  exposed to it. A later accidental retry of its source pull was stopped at about 5%; no model was
  installed and no inference occurred.
- No hosted-provider credential is configured for the local evidence runner.

Accordingly, no v9 holdout is authored. The next candidate must be a genuinely new non-Qwen base
family that supports strict structured output and a zero-thinking-byte transport. It must first
pass an already-exposed development packet; only two prospective development passes can authorize
a newly written, committed and pushed holdout.

## Exhausted local families

| Family | Best relevant frozen outcome | Status |
|---|---:|---|
| Qwen | 61/64 on v8 qualification | qualified, already represented |
| Phi | 58/64 on v8 qualification | failed per-axis gates |
| Llama | 59/64 on v5 qualification | failed per-axis gate |
| Gemma | 56/64 on v5; 19/24 on v8 development | failed |
| Granite | 55/64 on v5 qualification | failed |
| Command R | 55/64 on v5 qualification | failed |
| EXAONE | 52/64 on v7; 20/24 on v8 development | failed |
| InternLM | 53/64 on v7 qualification | failed |
| Falcon | 51/64 on v7 qualification | failed |
| GLM | 51/64 on v7 qualification | failed |
| OLMo | 46/64 on v7 qualification | failed |
| DeepSeek | 38/64 on v7 qualification | failed |
| Mistral | 20/24 on v8 development | failed |
| GPT-OSS | preflight abort before inference | transport incompatible |

Authoritative local receipts are in `reader-qualification-v5-2026-08-25`,
`reader-qualification-v6-2026-08-25`, `reader-qualification-v7-2026-08-25`, and
`reader-qualification-v8-2026-08-26`.
