# Ainglish evidence factory

This package supplies the orchestration that is intentionally outside the released SDK panel
harness. It validates digest-pinned campaign indexes and run specifications, rereads authenticated
live suggestions and proposal state, enforces per-campaign GPU contracts, refuses any campaign
that already has an attempt receipt, and then delegates the atomic mint-before-spend lifecycle to
`ainglish.panel._run_preregistered_panel`.

It does not turn two models into two principals, retry an outcome, resume an interrupted scientific
attempt, or reinterpret a null/adverse result. Those constraints belong to the evidence design.

Zero-cost validation:

```bash
PYTHONPATH=. /home/dexagon/codex/dexagon/.venv/bin/python -m evidence_factory.cli \
  path/to/campaign-index.json --show-gpus
```

Every index is sealed by `content_sha256`, computed from canonical JSON after removing that field.
Every runspec is separately pinned by `runspec_sha256`. A campaign-specific launcher injects the
local authenticated client and the official panel `ask` function; credentials remain outside this
repository and are never serialized into an artifact.

After each attempt settles or aborts, the runner asks every declared Ollama endpoint to unload its
model. This cleanup cannot change an observed result; it ensures that the next campaign must pass
its own frozen free-memory gate instead of inheriting a resident allocation.

Batch resumption skips a campaign only when a local measurement-request or abort receipt proves
that its attempt settled. Cell sidecars without either settlement receipt stop the batch for
reconciliation; they never license a second attempt.

## Evidence-design freeze

`design.py` adds a reusable pre-run design envelope for new reader-backed carriers. It creates and
validates digest pins for every answer-bearing item file and refuses unless:

- every declared form has exactly one careful-English claim carrier;
- bare English is a separately frozen diagnostic and cannot masquerade as the carrier;
- scientific and calibration counts match the item bytes;
- at least two qualified base-model lineages are required;
- mint-before-spend, both-arm calibration, no scientific retry, complete-pair identity, and
  retention of every admissible result are explicit gates; and
- claim-carrier and diagnostic campaigns do not reuse one complete input file.

Freeze an unsealed draft without a model, tokenizer, governance, or credential call:

```bash
PYTHONPATH=. python3 -m evidence_factory.design draft-design.json --output design.json
```

Campaign-specific builders still author the semantic items. The factory standardises the
evidential envelope around them; it does not generate answers or turn a design check into evidence.
