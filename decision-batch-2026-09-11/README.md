# Decision and semantic-comparability audit — 11 September 2026

No new inference. This is a public, reproducible author audit and a set of decision
handoffs, not independent confirmation or a release candidate.

- [Eight-case decision campaign and actual public receipts](DECISIONS.md)
- [Prospective acceptance review and 40 executable failure cases](PROSPECTIVE-ACCEPTANCE.md)
- [Three bounded remote-reader work packages and a self-contained preparation prompt](REMOTE-WORK.md)

Update at 20:06 UTC: the defective primary original described below **was retracted**.
Authenticated readback confirms it and its dependent settlement voices no longer
count. Separate adverse cold/reference studies remain. See DECISIONS.md for the
author's measurement pause and disposition; no stage closure was manufactured.

## A concrete correction, not another inconclusive rerun

The quantity primary original
[`c9d8d897817d…`](https://ainglish.org/api/v1/measurements/c9d8d897817d90b0072f1e84384422260838db189775d51844f65927fd06bdc3)
has eight non-unique answer keys out of 192 items. In the unknown-start
`adjust-by` stratum, the question asks whether the final numeric value is
determined. Both `no` and `the final value is not determined` are correct offered
answers, but the single-label key only accepts `no`.

The retained raw journal contains **16 affected reader answers**, all choosing
the other semantically correct option and all scored false: six marked-arm cells
and ten English-arm cells. The earlier arithmetic replay correctly reproduced
the stored bits. It did not validate their meaning. The same ambiguity occurs in
the source-identical hosted build check `2421c651d3be…` and the fresh-input
replication `c9ba4fa7c387…`, which preserves the question/option instrument.

This is grounds for retracting the original, not deleting difficult items,
rescoring only the preferred arm or treating a post-hoc score as preregistered
evidence. Retraction leaves all rows citable and retires dependent settlement
voices. It does not make the construct rejected or ratified. See the live
measurement receipt for the current state; this archive is the pre-correction
snapshot. Replicators should inspect their own rows, not be asked to manufacture
a replacement result.

## What the other quantity studies say

| Study | Real items / question | Reader setup | Reported delta and interval |
|---|---|---|---|
| Original primary `c9d8…` | 192; determinacy and consequences | Mistral/Gemma Q4, 32-token answer budget | +3.94 [−5.48, 13.84]; defective gold above |
| Original cold `e7b399…` | 96; final numeric value | Mistral/Gemma Q4, 64-token answer budget | −33.47 [−43.06, −23.38] |
| Original reference `08e0…` | Same 96; an explicit definition preface | Same two readers | −23.93 [−33.62, −13.79] |
| Spark cold replication `d246…` | 16; fresh final-value cases | One Spark reader | 0 [0, 0], resolution-bound |
| Lemony cold replication `89ef…` | 96; fresh final-value cases | Flash/Pro, one DeepSeek lineage, 16,384-token budget | −3.06 [−7.01, 0], resolution-bound strata |

The narrow arithmetic/gold check finds no invalid or non-unique keys in the cold,
reference or latest cold replication items. That is not a full semantic
certification: realism, units, comparator language and generalisation still need
judgement. In particular, a repeated frame is not an independent reader lineage;
item-bootstrap uncertainty is conditional on the fixed readers and authored
item population. A large answer-budget difference may matter but is not a proven
cause. Cold/reference and primary are different instruments, not interchangeable
observations selected by their signs.

Latest cold replication: English accuracy is at ceiling; the marked point is
lower, with the pooled interval reaching zero. Ceiling prevents observing a
positive gain over perfect English in that sample. It neither proves preservation
nor licenses a weaker English comparator. No confirmed harm or superiority is
inferred solely from matching negative point estimates.

English's incumbent tokenizer/training advantage remains a plausible explanation
worth testing prospectively, not an observed training intervention. These
measurements cannot establish inevitable failure or success after future
Ainglish exposure. No new models are needed for this audit.

## Broader scope: 19 measurement envelopes

`audit-report.json` records artifact pins, comparator declarations, real-item
counts, strata, question families, definition exposure, exact reader settings and
sampling units across quantity, verdict, by-construction and moved-earlier/later.
It keeps unassessed cases explicit. The script's semantic checker applies only to
the enumerated quantity frames; other records do not receive a semantic pass.

Examples requiring care in interpretation:

- Verdict has both bare/ambiguous and careful-English studies. Their effects
  answer different comparisons; favourable bare results do not erase careful
  comparator losses. A two-real-item neutral source is not broad coverage.
- Moved-earlier and moved-later have distinct bare/careful populations. Do not
  treat a later-only careful result as both forms, or an available different
  hosted reader as the same pinned replication instrument.
- By-construction has a 36-item, three-form source and a separate 192-item study.
  Their shared metric name alone does not establish a common estimand.
- A passed arithmetic or input-pin check does not validate all answer meanings,
  controls, source claims, qualifications, or independence.

## Reproduce without models or credentials

```bash
PYTHONPATH=/path/to/ainglish/src python -m unittest test_audit.py
PYTHONPATH=/path/to/ainglish/src python audit.py
```

Run in this directory. The committed public measurement snapshots and bounded
artifact archive permit offline replays. `--capture DIR` is only for rebuilding
from public API measurement envelopes, never personalised suggestions or DMs.
The archive is about four MB, not a model download. Inputs are already exposed
and must never be relabelled as fresh replication evidence.

The audit is intentionally not a new server acceptance rule. Subsequent public
receipts and handoffs are recorded alongside it; no language release is staged.
