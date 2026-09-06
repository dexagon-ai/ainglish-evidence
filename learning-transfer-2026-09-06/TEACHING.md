# Ratified teaching supplement — 336 examples

`teaching-supplement-336.zip` is a non-normative, CC0, training-only supplement
from this study's frozen curriculum. It is **not a new language release**.

- Archive SHA-256: `fdc4d436d131676915eed9484e1db945c59d9d17243fc8e7ac0182483a2347dc`.
- 336 paired examples, six ratified families, 42 frames and eight lexical domains.
- English and Ainglish training arms are separate; the archive retains provenance
  and the exact source definitions used to construct the examples.
- Holdout tasks, composition evaluations, answer-bearing evaluation records,
  model outputs and adapters are excluded by an explicit export allowlist.
- `TEACHING-MARKER-AUDIT.json` records literal marker checks against a dated
  all-stage catalogue. Training messages have no additional registered marker
  strings beyond their taught families. This is not a proof of all semantic
  dependencies, nor a claim that every marker mentioned inside an archived
  definition is itself ratified.

The contents are identical to the curriculum frozen before training at
`73df9ce`. They have not been improved retrospectively using the failed holdout.
The source definitions are reference metadata, not text silently appended to
every training message. The small ZIP does not contain a model or require any
model download. `export_teaching.py` reproduces the audited export and refuses
to overwrite an existing artifact.

Use these examples with the limitations in `RESULTS.md`: one cached base model,
three seeds and synthetic frames did not establish a repeatable learning
advantage. Inclusion in a training corpus would be an adoption receipt, not
proof of better comprehension or a change to a tokenizer.
