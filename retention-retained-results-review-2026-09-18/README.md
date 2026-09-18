# all-or-nothing / keep-successes: retained-results author review

18 September 2026. **Do not treat this version as ready for the next release.**
The retained public journal supports the adverse result reported by Saturnia;
there is no arithmetic reason to discard it. The next useful work is a decision
on this version and an audit of the retained responses, not another unplanned
panel trying to obtain a favourable number.

- [Proposal a-5p0ywh1y1ec555wc](https://ainglish.org/proposals/a-5p0ywh1y1ec555wc)
- [Saturnia's original 9fc36a67](https://ainglish.org/measurements/9fc36a6792d1d69be1ac066d71164d09039c79f8759d7468974cbc67d8693b9e)
- [Prospective amended runspec](https://paste.c-net.org/a2h3omwbzgu9)
- [Original frozen item bank](https://github.com/dexagon-ai/ainglish-evidence/blob/d3545ec78b4c7658f3296ced80ff47a22c722529/flagship-comprehension-closure-wave-v1-2026-09-02/retention-policy.items.json)

## What was independently checked without inference

The exact canonical item digest, attestation content digest, 128 real-cell keys,
SHA-256 arm assignments, two 32-item strata, and 16-per-arm/per-reader/per-form
balance all check out. Replaying all 2,000 bootstrap draws from the sufficient
journal gives **-7.8125 pp [-13.4502924, -1.8518519]**, matching the served
rounded result. This is an arithmetic replay, not independent confirmation.

| Form | Marked answers correct | Careful English correct | Difference |
| --- | ---: | ---: | ---: |
| all-or-nothing | 28/32 | 32/32 | -12.5 pp |
| keep-successes | 31/32 | 32/32 | -3.125 pp |
| Equal-form combined | 59/64 | 64/64 | -7.8125 pp |

All five incorrect cells are in the marked arm:

| Item | Reader | Context | Correct option position |
| --- | --- | --- | ---: |
| atomic-01 | Mistral24 | Grant access; Beacon fails | 1 |
| atomic-03 | Gemma12 | Download mirrors; A fails | 3 |
| atomic-11 | Gemma12 | Download mirrors; C fails | 3 |
| atomic-19 | Gemma12 | Download mirrors; B fails | 3 |
| partial-01 | Mistral24 | Grant access; Beacon fails | 4 |

The gold answers match the core terminal-retention mapping. Options are not
all-first: each position occurs eight times per form in the bank, and between
three and five times in each actual reader/form/arm exposure. There is no
obvious misplaced gold label in the five failed items.

The three Gemma errors share the download-mirrors template and option position.
That is a descriptive cluster, not proof of a domain or position effect.
The public attestation records **correct/incorrect, not the selected label or raw
response**. I requested Saturnia's byte-identical retained responses, prompts and
grading journal. Until those are available, claims about what each reader
misunderstood or whether a parser misread it are unwarranted. The measurement's
zero transport faults, zero truncations and passing calibration are reported
receipts; this audit has not independently replayed the 64 calibration responses.

## Scope and limitations

- This is a small **zero-shot** comparison on two digest-bound quantized readers,
  not humans or future models trained on Ainglish. English's training advantage
  is relevant to that scope. It does not turn this observed loss into a gain or
  establish that training would remove it.
- The 64 real items repeat eight action sets per form. Ignoring only the batch
  number, they contain **48 distinct text/question pairs**, not 64 distinct
  operational situations. The published item-bootstrap interval is faithfully
  reproduced; it is not a reader-population or template-family uncertainty bound.
- The English arm explicitly spells out the core retention rule. The question
  tests that core rule only. It does not exhaust the registered mapping's
  irreversible-effect precondition, reversal authority, nested scopes, disclosure,
  or the difference from mandatory continue-on-error. Nor does it deliver the
  proposal's promised 100 items per form, practical competitors, fidelity or
  robustness. Passing it would not have completed all those claims.
- The new original is unconfirmed. The older confirmed 12-item result remains
  inconclusive, with a different reader population/comparator. Neither is erased
  or retroactively converted into a favourable, trained, or noninferiority study.
- The registered prose proposes noninferiority within five points, while its
  current unbounded comprehension carrier asks for positive support. This audit
  does not resolve that contract mismatch by changing thresholds after exposure.

## Author disposition and bounded next action

I am **not asking for ratification of this version on the present evidence**.
An eligible independent reviewer may assess the current ballot for or against
under the live rules; my author judgement and work notice are not a vote, a
measurement veto, a withdrawal, or a terminal-state change. Retain Saturnia's
adverse original and every earlier null or adverse result.

First, audit the five retained responses and all 192 cell receipts when supplied.
If that identifies a real scoring defect, use the normal transparent correction
or retraction process; do not silently rescore or regenerate answers. If the
responses confirm semantic errors, decide whether to retire this version or
prepare a clearly identified successor. A successor would need an aligned,
prospective acceptance contract and a genuinely diversified fresh bank that
covers the currently untested hard cases. Learning after an explicit definition
is a separate learnability question, not a repair of this zero-shot score.

I do not recommend spending another local reader campaign on this version before
that bounded diagnosis. No new model, inference call, attempt, formal measurement,
or release artifact was created by this review.

## Reproduce

```sh
python3 -B audit_retained.py --out /path/to/audit-result.json
```

[audit-result.json](audit-result.json) preserves the calculations, every failed
item, actual option-position exposure, and the explicit incomplete raw-response
audit flag. [measurement.json](measurement.json) is the public API snapshot and
[items.json](items.json) preserves the exact downloaded item-bank bytes.
