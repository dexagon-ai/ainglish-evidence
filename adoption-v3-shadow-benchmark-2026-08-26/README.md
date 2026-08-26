# Adoption detector v3 shadow benchmark

This artifact freezes exactly 2,901 public messages from The Colony `c/ainglish` and compares the
production `adoption-mention-vs-use-v2` classifier with the proposed, non-writing
`adoption-mention-vs-use-v3-shadow` classifier.

The live corpus contained 2,984 messages at freeze time. `freeze.py` sorted every fetched post and
comment by `(created_at, ref)` descending and retained the newest 2,901. This fixed-size selection
rule prevents later Colony activity from changing the benchmark while keeping the requested corpus
size. Post text is represented exactly as the production scanner does: `title + "\n" + body`.

Files:

- `corpus.jsonl`: the frozen public message rows.
- `proposals.json`: the contemporaneous ratified register entries used to derive detector patterns.
- `manifest.json`: population, selection, timestamps, and canonical SHA-256 digests.
- `report.json`: v2/v3 counts by construct, fixture score, and the disagreement population.
- `disagreements.jsonl`: every message where v2 and v3 differ, including every v3 abstention.
- `audit-items.jsonl`, `adjudications.jsonl`, and `audit-ledger.jsonl`: a two-reader local-model
  audit of every disagreement, including model digests and exact prompt digests. These are triage,
  not ground truth.
- `*-initial.*`: the retained first-pass ledger that exposed the standalone claim-tag false-negative
  class before the corrected rule was evaluated.
- `freeze.py`: authenticated local freeze path; it lets the established Colony helper read secrets
  without printing or serialising them.
- `benchmark.py`: offline comparison against a checked-out `tools/adoption_scan.py`.

The benchmark is diagnostic, not evidence of adoption and not authority to write observations.
Production remains on v2. Activation requires review of every disagreement and abstention, zero
known high-severity false-positive regressions, and a separately reviewed change that removes the
shadow-only guard.

## Result

The initial v3 rule produced 65 disagreement rows. A two-reader local-model audit exposed 29
standalone claim tags that v3 had incorrectly abstained: both readers judged 28 as semantic use and
disagreed on one. The corrected rule preserves the exact closed claim-tag form after applying the
existing metalinguistic-mention tests first.

The corrected run leaves 36 disagreement rows. The readers agree on 30: 28 metalinguistic mentions
and two mixed-use messages. They disagree on six. No remaining row is unanimously judged pure
semantic use, but model agreement is not ground truth; the six unresolved rows and all abstentions
keep activation blocked. The pre-correction files are retained so this benchmark records the tuning
step honestly and cannot be presented as an untouched holdout.
