# Reader qualification calibration v1

This package diagnoses the terminal v7 no-roster result without changing it. V7 remains an
immutable 384-cell screen in which no reader qualified, no roster became ready, and no scientific
Ainglish campaign may be minted.

The offline response matrix found 28/64 items with six-reader key support, 17/64 with at most three
supporting readers, and three with zero support. The three unanimous misses are familiar inference
traps: affirming the consequent, denying the antecedent, and resolving an ambiguous pronoun as if
it had a unique antecedent. All 17 low-support keys received a semantic engineering review. Sixteen
remain defensible; one normative only-rule item remains defensible under the phrase “under this
rule” but is wording-sensitive enough for one optional native-speaker judgment.

A second instrument issue cuts across several misses. V7 mixed direct questions with polar
meta-questions such as “does the sentence establish…?” Under that form, `no` means the embedded
claim is not established, while readers may instead choose `cannot tell` about the embedded claim.
Consensus is therefore useful for locating confusing cells, but is not a truth oracle and is not
used to re-key or rescue v7.

`development-packet.json` is the corrective exposed-control packet. It uses one contract throughout:
given a premise, classify a hypothesis as `entailed`, `contradicted`, or `not determined`. Its 24
fresh items are balanced across eight semantic axes, the three labels, and all three opaque answer
positions. It is development-only and can never qualify a reader or count as proposal evidence.

`run-plan.json` freezes a single diagnostic pass over the six already-pinned v7 readers. It makes
no pass/fail decision. Every cell is attempted at most once, all outcomes are retained, thinking
must remain disabled, and the plan and packet are committed and pushed before the first call.

## Development outcome

The frozen run completed all 144 cells with zero thinking bytes and zero transport faults. It
returned 143 exact opaque codes and 110 correct labels. Performance was sharply label-dependent:
`entailed` scored 44/48, `contradicted` scored 48/48, and `not determined` scored 18/48. Thirty of
the 34 errors were on the last label, and the fresh ambiguous-pronoun control received zero key
support. The uniform contract therefore removed one instrument-form ambiguity but did not remove
the readers' systematic tendency to infer a likely completion from incomplete information.

The next permitted development step is one prospectively frozen generic clarification of the
three labels, deliberately reusing these exposed controls. It must define the labels in terms of
all situations consistent with the premise and warn against choosing the most likely completion.
Any tuned result remains development-only; only a later untouched and disjoint v8 holdout can
qualify readers.

`tuned-run-plan.json` freezes that sole revision. A reader passes the development screen only with
24/24 exact codes, at least 22/24 correct, at least 2/3 per axis, at least 7/8 per label, zero
thinking bytes, and zero fault cells. A fresh v8 holdout should be authored only if at least two
distinct lineages pass. The gate and exact instruction are committed before the tuned calls.

## Tuned outcome

No reader passed the prospective development gate. The clarification improved `not determined`
from 18/48 to 25/48, but overall correctness fell from 110/144 to 105/144 and exact-code compliance
fell from 143/144 to 135/144. InternLM 2 came closest with 22/24 correct and 24/24 exact codes, but
its `not determined` score was 6/8 rather than the required 7/8. The clarification also induced
several code-plus-label or truncated-label outputs under the unchanged four-token bound.

This is a mixed and overall adverse development result. `v8_authoring_ready` is false. Repeatedly
tuning these exposed controls would overfit the instrument, so this branch stops here: preserve the
one optional native wording check, separate constrained formatting from semantic discrimination,
and identify a genuinely stronger new lineage or prospectively frozen constrained-decoding
transport before further GPU spend.

The package can be reproduced and audited offline with:

```bash
python3 analyze.py
python3 build_development.py
python3 build_run_plan.py
python3 analyze_development.py
python3 analyze_tuned.py
python3 audit.py
python3 audit_tuned.py
```

The optional human burden is deliberately one item, in `native-review-packet.json`. Any answer
affects only future instrument wording and cannot alter v7's result.
