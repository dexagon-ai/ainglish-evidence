# Adversarial semantics gauntlet result

Status: **complete**

All 54 preregistered model calls completed, expanding to 540 scored cells. Every batch satisfied the
exact answer-channel contract; there were no malformed batches, empty-content failures, retries, or
model downloads.

Raw response SHA-256:
`4add7a99dbe58df8db6e61d6d23c77195127b780d8d68c7653e58e91e816b659`.
Analysis content digest:
`895725fa63c695ec1e9839dd4f8249d5add4615509d6452a2070028a10ad7fa4`.

## Reader results

| Installed reader | Correct | Accuracy | Invalid cells |
|---|---:|---:|---:|
| `gemma3:12b` | 172/180 | 95.6% | 0 |
| `mistral-small3.2:24b-instruct-2506-q4_K_M` | 170/180 | 94.4% | 0 |
| `qwen3.5:9b` | 160/180 | 88.9% | 0 |

These are reference-grounded application results: every prompt supplied the exact construct meaning.
They are not cold-comprehension or human-intuitiveness estimates.

## What the gauntlet exposed

Across readers, quoted opposite-pole distractors were perfect (`108/108`). Direct entailments reached
`103/108`, dual-record scope isolation `104/108`, boundary-overread rejection `98/108`, and curated
cross-form relations `89/108`. The hard part was therefore not copying through quoted noise; it was
reasoning about what a marker leaves open and about asymmetric relations between two displayed forms.

Of the 38 errors, 19 occurred where the correct label was `underdetermined`, 11 where it was
`entailed`, and 8 where it was `contradicted`. Twenty-seven wrong answers chose `contradicted`. The
dominant failure mode is treating “the marker does not assert this conclusion” as “the marker asserts
this conclusion is false.”

Two cells failed identically on all three readers:

- From `some-or-all workers may retry`, every reader labelled “Every worker definitely will retry”
  contradicted. The frozen semantics leave that future outcome open; permission for some-or-all does
  not guarantee it, but does not rule it out either.
- From `restore-state(open(gate)): Mara opened the gate`, every reader labelled an earlier matching
  gate-opening act by Mara contradicted. The construct commits to the earlier state, while the actor
  and event that produced it remain underdetermined.

These unanimous errors are useful documentation and prompt-design targets. They do not by themselves
show that the reference is wrong; both items deliberately distinguish non-entailment from negation.

## Construct diagnostics

Seven constructs were perfect on this finite battery across all three readers:

- `no-delegation / one-hop-delegation-allowed`
- `each-alone / as-one`
- `or-both / not-both`
- `moved-earlier / moved-later`
- `whole(S) / part(S)`
- `proposal-by(P) / decision-by(A)`
- `text-fixed(ref) / meaning-fixed(ref)`

The weakest aggregate rows were `one-or-more / exactly-one` (`23/30`), `true-as-worded /
false-as-worded` (`24/30`), `among-others / and-no-others` (`25/30`), and `repeat-event /
restore-state` (`25/30`). `some-or-all / some-but-not-all` and `may-as-permission /
may-as-possibility` each reached `26/30`; `start-by / complete-by` reached `27/30`.

The cardinality row exposed both directions of its asymmetric relation: some readers overread
`one-or-more` as exactly one, while others failed to infer at least one from `exactly-one`. The
negative-question row produced repeated failures on the `false-as-worded` pole even when the full
reference was present. That repeats the separate agent-task benchmark's internal warning about this
surface, but the two project-operated tests are not independent confirmation.

## Consequences

1. Public explanations should teach “not stated” versus “stated false” explicitly, especially for
   modality, quantities, and state restoration.
2. `true-as-worded / false-as-worded` needs targeted redesign or much stronger negative-question
   examples before it is treated as an uncomplicated flagship, despite being ratified.
3. `one-or-more / exactly-one` should retain both directions of the asymmetry in every reference and
   test: exactly one entails at least one; at least one sets no upper bound.
4. `repeat-event / restore-state` should state that restoration commits to a prior state, not to the
   identity of the earlier actor or event.
5. Perfect rows remain promising examples, not proven human-facing winners; their ten cells per
   construct are a regression battery rather than broad validation.

## Claim boundary

This is a deterministic, project-designed, project-operated development diagnostic over three
already-installed model artifacts. It can reveal reference, harness, and semantic-boundary risks. It
cannot establish human understanding, independent evidence, training-data inclusion, external
adoption, lifecycle standing, or ratification readiness, and it is not submitted as governance
evidence.
