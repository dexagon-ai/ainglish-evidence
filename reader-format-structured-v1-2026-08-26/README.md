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

## Outcome and recovery note

All 72 calls completed and the journal recorded its terminal `run_completed` event. The original
runner then raised a `KeyError` while mapping suffixed gate names such as
`valid_json_cells_required` to observed names such as `valid_json_cells`; no result file had yet
been written. No cell was rerun. `recover_result.py` validates the attempted/recorded sequence and
reconstructs the result solely from the durable journal, while preserving the missing historical
preflight-detail limitation in the result.

Every response was valid JSON and exactly matched the one-field schema. Seventy-one of 72 copied
the explicit target correctly. Five readers passed 12/12; InternLM 2 returned `C` for one explicit
`A` target and therefore failed the strict compatibility gate at 11/12. This establishes that JSON
schema removes response-shape faults for all six readers, but constrained syntax does not guarantee
correct choice selection and cannot repair semantic over-inference.
