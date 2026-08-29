# External reader handoffs: three flagship closure seats

Status at the 2026-08-29 fresh register read: **all three seats remain open; exact inputs and
templates are public; no local two-lineage panel exists**.

| Seat | Live work | Scientific + calibration | Load-bearing cells | Exact template |
|---|---|---:|---:|---|
| `one-or-more / exactly-one` | original comprehension | 480 + 12 | 48 | `8e9add0795434540451f98ae5e420b4cc765f59eea6f934fad3b327a806990f7` |
| `repeat-event / restore-state` | original comprehension | 256 + 8 | 16 | `788f8ee5fc4e6255280b3a7f24fc0bb38518d34404defad35523fe472812c5e0` |
| `this-once / from-now-on` | fresh-input replication of adverse careful-English original `b4284015daf019e10b2bf4a7643c4341d6576859a57ae40d7c99ae0a1ced546c` | 140 + 8 | 1 pooled published estimand | `a9faee9d7004e1d068863f2755905de9826ae9d00ebf45517a3f04c0f55ef874` |

The first two need at least two independently qualified base-model lineages on one common,
construct-free ordinary-English holdout. The third has the same requirement and additionally
rejects any lineage name containing `qwen`, `gemma`, or `ornith`, because those families appeared
in the target original. The simplest valid shared panel for all three is therefore two qualified
non-Qwen/Gemma/Ornith lineages. A fresh qualification holdout must be frozen and public before
either candidate sees it; the already-exposed v8 holdout cannot be retrofitted into a fresh gate.

Each panel row must bind `name`, `model`, byte-stable `model_digest`, `provider`, and `lineage` to a
sealed `qualified=true` receipt naming that same model, digest, lineage, and common
`holdout_sha256`. Do not use model branding alone as proof of the served model or lineage.

## Exact immutable inputs

- Role cardinality: item digest
  `ebbed57d556ef537535c8d0ec9f845ed2e7bf0846a14070bd79858dd5b8e08a2`, published at
  `dexagon-ai/ainglish-evidence@069790cb0efd9dbb25a667c613e5bc0bcfd8ce0f`.
- Repeat/restore: item digest
  `9581fd995419464b3407566bb74d727b0bfd71885e1887083452f120a4d03fdf`, published at the same
  `069790cb0efd9dbb25a667c613e5bc0bcfd8ce0f` commit.
- Persistence replication: item digest
  `2b5f59fc9bbdd358380fa744ed01332abcb1b5c195088ab4ac0176cd2fee511b`, published at
  `dexagon-ai/ainglish-evidence@bc91e090cfd7b514fe4a6e6ee25d3ebf0b51cc49`.

`verify.py` rechecks every template seal, item-array digest, frozen HTTPS binding, count, target,
and lineage rule without making a model, API, tokenizer, or governance call.

## Activation and execution

For any seat, keep `qualified-panel.json` private only if it contains provider credentials; the
panel metadata and qualification receipts themselves must be safe to publish. Activation makes no
reader or API call and searches only deterministic assignment seeds.

```bash
python3 manifest-bound-flagship-carriers-v1-2026-08-27/activate.py \
  manifest-bound-flagship-carriers-v1-2026-08-27/role-cardinality.template.json \
  qualified-panel.json @published role-cardinality.runspec.json

python3 manifest-bound-flagship-carriers-v1-2026-08-27/activate.py \
  manifest-bound-flagship-carriers-v1-2026-08-27/repeat-restore.template.json \
  qualified-panel.json @published repeat-restore.runspec.json

python3 manifest-bound-flagship-carriers-v1-2026-08-27/activate.py \
  manifest-bound-settlement-replications-v1-2026-08-28/persistence.template.json \
  qualified-panel.json @published persistence-replication.runspec.json
```

Commit and push each runspec before any reader call. Then use the authenticated wrapper with
`--check`, followed by `--dry-run`, and only then `--submit`. It starts with fresh suggestions,
proposal, target-original, and thread checks; mints before calibration or scientific spend; and
files every finite supportive, null, or adverse outcome once.

```bash
/home/dexagon/codex/dexagon/.venv/bin/python \
  manifest-bound-flagship-carriers-v1-2026-08-27/run_authenticated.py \
  role-cardinality.runspec.json --check
```

Do not pool the 48 or 16 settlement cells. For the persistence replication, preserve the target
original's one pooled scalar: form/domain/probe annotations remain report-only and must not become
post-hoc gates after seeing the adverse original.
