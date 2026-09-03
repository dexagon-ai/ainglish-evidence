# Remote reader qualification wave v2

This is a no-download qualification wave. It contains two prospective remote
model-family slots (Anthropic/Claude and OpenAI/GPT) plus two exact local Ollama
readers already retained on disk (Qwen 3.8 27B and Mistral Small 3.2 24B). The
remote family names are selection slots, not sufficient reader identity. Before
either remote run, replace its placeholder endpoint and model with the exact
provider catalog values and publish that changed screen. A routed alias remains
provider-opaque and must not be described as immutable weights.

Both candidates use the same 16-item, construct-free positive-control screen.
The controls cover ownership, authorization, temporal order, quantifier scope,
reference, negation, causation and revision state.  Each detectable arm resolves
two explicit alternatives; its paired other arm leaves the choice unresolved.
Answer positions are balanced.  The screen contains no Ainglish marker and is
not proposal evidence.

Generate and validate without network or inference:

```bash
python3 build.py
ainglish-qualify-reader check anthropic-claude.screen.json
ainglish-qualify-reader check openai-gpt.screen.json
ainglish-qualify-reader check local-qwen38-27b.screen.json
ainglish-qualify-reader check local-mistral-small32-24b.screen.json
```

After an operator supplies one exact raw, stateless OpenAI-compatible endpoint
and its credential through the named environment variable, run that candidate
once:

```bash
ainglish-qualify-reader run anthropic-claude.screen.json -o anthropic-claude.result.json
```

There are no retries.  Preserve a failure or transport fault as the result.  A
pass qualifies only the exact endpoint/model/precision/settings receipt until
its expiry; two endpoints routing one underlying family are not two lineages.
Do not expose a proposal's answer-bearing carrier until two genuinely distinct
lineages pass this common screen.

The local screens bind the exact digest through Ollama's `/api/tags` immediately
before the one-shot run. They do not download or alter model weights. Publish
the generated screen files before making any reader call.

## Local one-shot outcomes

- `local-mistral-small32-24b.result.json`: passed (16/16 detectable; 3/16
  other), exact model digest and settings recorded in the receipt.
- `local-qwen38-27b.result.json`: failed (6/16 detectable; 0/16 other). The
  frozen 64-token transport budget produced truncations. This result is retained
  as run, with no tuning or retry on the exposed controls.

Only the passing Mistral receipt may be attached to a proposal measurement.
One local pass is not the two-lineage gate required before target exposure.
