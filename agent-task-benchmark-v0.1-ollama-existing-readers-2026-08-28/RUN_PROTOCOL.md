# Frozen run protocol

Frozen at: `2026-08-28T22:22:14Z`

Benchmark commit: `028052715cfa61744fab0ca92268f71073de2246`

Task-packet SHA-256: `e29e18435ed8ab7ac2144a1ce57ca943b2d82c6568b32a8c1bae7935690f5bdf`

Schedule seed: `2026082801`

## Readers and exclusions

The reader allowlist is fixed in `run_ollama.py`. Preparation resolves every tag to the digest and
complete served metadata returned by the already-running local Ollama server. It aborts if any tag is
missing. It does not call a pull endpoint.

The allowlist contains the distinct, explicitly named general-purpose chat/base tags selected before
inference. It excludes:

- every `dexagon-*` tag, because those aliases carry task-specific system prompts or adapters;
- `hf.co/*` aliases and other duplicate digests, to avoid counting the same served artifact twice;
- incomplete Hugging Face cache entries; and
- embedding-only or otherwise non-chat artifacts.

Different tags are repeated machine readers. They are not independent research participants merely
because they have different names. Shared model ancestry may create additional dependence.

## Cells and order

There are 22 items, three arms, and two exposure tracks: 132 cells per reader. All cells are created
from the frozen benchmark's `prompt_for` implementation and globally shuffled once with the fixed
schedule seed. Every reader receives the same order. Each cell starts a fresh chat conversation.

The tracks have different estimands and are never pooled:

- `cold` supplies no definition and measures immediate prompt-cold compatibility. Training exposure
  remains unknown.
- `one_exposure` supplies the frozen one-use reference only to the Ainglish arm. Its tokens are part of
  the treatment cost. It does not estimate pretrained adoption.

## Inference contract

Transport: local Ollama `/api/chat`, non-streaming.

Frozen request parameters:

```json
{
  "format": "json",
  "keep_alive": "15m",
  "options": {
    "num_ctx": 4096,
    "num_predict": 96,
    "seed": 20260828,
    "temperature": 0
  },
  "stream": false,
  "think": false
}
```

The benchmark prompt is the sole first-turn user message. The response is parsed with strict JSON
decoding after removing only surrounding whitespace, then checked against the benchmark's exact
decision schema and available action IDs. Markdown fences, prose, extra keys, unknown actions,
refusals, and empty outputs are invalid. The exact raw output is always retained.

If and only if the first decision is `clarify`, one repair request is made in the same conversation:

```text
Clarification from sender: <the frozen scripted clarification>

Respond under the original JSON-only contract.
```

The repair must be an exact valid `act` object. No clarification is sent after an action or invalid
response. Provider token counts are recorded per call and summed for repaired cells; consequently the
repair input count includes the conversation prefix processed again. Latency is Ollama's
`total_duration`, including load time, with client wall time retained separately and used only if the
server omits its duration.

## Failures, interruption, and retries

There are no inference retries. A transport error, timeout, parser failure, or refusal is an observed
failure and remains in the denominator.

Before each inference request, the runner atomically writes an in-flight receipt. A completed cell is
atomically appended and synced before that receipt is cleared. On restart:

- interruption during the first request becomes an invalid first response;
- interruption during the permitted repair preserves the first clarification and records a missing
  repair; and
- completed cells are never run again.

This conservative rule prevents a crash from creating an outcome-dependent retry. Runs are sequential
(`parallelism = 1`) to avoid changing quantization or placement through local GPU contention. The
runner unloads a reader after its complete block; unload requests are administrative and not
inference.

## Analysis and claims

The primary comparison is the paired, item-level difference in zero-repair success between Ainglish
and careful English, separately for every reader and track. For each pair, report the mean difference,
Ainglish-only successes, careful-only successes, and ties. Ainglish versus bare English is secondary.
Final success, clarification, wrong action, invalid output, tokens, and latency remain separate
outcomes; no composite score allows token savings to cancel a wrong action.

Results are also stratified by construct. Across-reader summaries are descriptive distributions of
reader-level paired effects, without manufactured call-level confidence intervals. Adverse and null
results are retained.

This project-operated run can inform task performance and expose failure modes. It cannot establish
human intuitiveness, independent replication, external adoption, general model-family benefit,
training-data inclusion, future tokenizer efficiency, or Ainglish superiority overall.

