# Remote reader qualification wave v2

This is a no-download, no-inference qualification wave for two model families
not present in the retained on-disk lineage audit: Anthropic/Claude and
OpenAI/GPT.  The family names are selection slots, not sufficient reader
identity.  Before either run, replace its placeholder endpoint and model with
the exact provider catalog values and publish that changed screen.  A routed
alias remains provider-opaque and must not be described as immutable weights.

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

