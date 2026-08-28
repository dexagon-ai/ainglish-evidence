# Manifest-bound flagship settlement replications v1

Five fresh-input comprehension populations are prepared for unsettled flagship originals:

- `moved-later` and `moved-earlier` versus their complete careful-English meanings;
- `may-as-permission / may-as-possibility`;
- `rather-not / fine-either-way / would-welcome`;
- `this-once / from-now-on`.

The two moved targets are positive or near-neutral; the may target is positive; preference and
persistence are adverse. Direction never changes the filing obligation. The answer-bearing source
populations were already frozen without reader spend, and this package changes no answer. It adds
one mechanical `settlement_stratum` label to each scientific row and leaves calibration rows
outside the estimand.

## Estimand boundary

Each target original published one pooled scalar. This package preserves that scalar. Existing
form, domain, voice, power, probe, attachment, and semantic-cross-cell labels remain valuable
diagnostics, but they are not promoted into new settlement gates after the original result is
known. The single load-bearing stratum is therefore `original-published-scalar`.

Every original used Qwen, Gemma, and Ornith readers. Activation requires two qualified lineages
whose declared family names contain none of `qwen`, `gemma`, or `ornith`, both qualified on the
same fresh ordinary-English holdout. Each embedded qualification receipt is byte-sealed and must
match the panel model, digest, and lineage. This is stricter than merely bringing fresh item rows;
it keeps the confirmation reader substrate disjoint too.

## Reproduction and execution order

The item freeze and template freeze are deliberately separate commits. The immutable item URL
must exist before a template can name it.

```bash
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python \
  manifest-bound-settlement-replications-v1-2026-08-28/capture.py
python3 manifest-bound-settlement-replications-v1-2026-08-28/build.py
python3 manifest-bound-settlement-replications-v1-2026-08-28/audit.py

# Commit and push the five *.items.json files, then bind that exact commit:
python3 manifest-bound-settlement-replications-v1-2026-08-28/build.py \
  --item-commit <full-first-item-commit>
python3 manifest-bound-settlement-replications-v1-2026-08-28/audit.py \
  --require-templates --write
```

After a qualifying panel exists, activate one template with the shared receipt-enforcing tool,
commit and push the runspec, then use the authenticated wrapper's `--check` and `--dry-run` modes.
Only then use `--submit`. The wrapper starts with authenticated suggestions and fresh proposal and
target reads; the SDK mints before calibration or scientific reader spend and either files the
finite result or publishes an evidenced abort.

No model or tokenizer call occurs in capture, build, audit, or activation. No attempt is minted
until a published runspec reaches the final `--submit` command.
