# Structured-output format compatibility v1

This is a format-only development diagnostic. It asks each of the six already-pinned v7 source
readers to copy an explicitly supplied target code into a one-field JSON object constrained by an
Ollama JSON schema. It contains no semantic premise, hypothesis, proposal construct, or hidden
answer key, so it cannot tune semantic judgments or qualify a reader.

The 12 controls contain four targets each for `A`, `B`, and `C`. A reader is format-compatible only
if all 12 responses are valid JSON, contain exactly the `answer` field with an allowed code, copy
the supplied target correctly, emit zero thinking bytes, and encounter zero faults. Every cell is
attempted once and journaled before its request.

The transport is pinned to local Ollama 0.32.7 and the official structured-output contract at
https://docs.ollama.com/capabilities/structured-outputs. The plan is committed and pushed before
the first call. A compatible result demonstrates only that constrained decoding can separate
format compliance from semantic discrimination; it does not rescue any earlier score.

Offline reproduction and audit:

```bash
python3 build_plan.py
python3 audit.py
```
