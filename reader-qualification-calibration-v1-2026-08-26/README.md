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

The package can be reproduced and audited offline with:

```bash
python3 analyze.py
python3 build_development.py
python3 build_run_plan.py
python3 analyze_development.py
python3 audit.py
```

The optional human burden is deliberately one item, in `native-review-packet.json`. Any answer
affects only future instrument wording and cannot alter v7's result.
