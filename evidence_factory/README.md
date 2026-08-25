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
