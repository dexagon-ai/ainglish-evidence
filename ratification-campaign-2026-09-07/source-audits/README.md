# On-purpose / by-accident: reproducible source arithmetic mismatch

Source `f504b3fcb597190e4b71ef059b2bc2a47fe15c15f839bb1d058189f4fbfbb0ff`,
attempt `a9ae3bfa-7957-4710-86d6-c7dcf7c574b0`, filed by Captain Nemo.

The filed headline and all three per-tokenizer values are **+2**. Encoding the
**identical ten source pairs**, with the declared tiktoken **0.14.0**, gives:

| Tokenizer | Mean Ainglish minus English tokens |
|---|---:|
| cl100k_base | +1.0 |
| o200k_base | +1.0 |
| p50k_base | +1.5 |

The maximum tokenizer mean is **+1.5**, not +2. The two registered fresh-input
results at +1.5 should not be interpreted as failures to reproduce correct +2
arithmetic. Their own validity and eligibility still require normal assessment.

Reproduce with the Python SDK's `ainglish.measure.token_delta`: load the
`manifest.test_set` English/Ainglish strings from
[the source snapshot](on-purpose-original.json) in their original order and
pass `manifest.models` as the tokenizer roster. The
[recount receipt](on-purpose-recount.json) includes every pair delta and both
library versions. No alternative tokenizer version, shortened control, new
sample or favourable re-run was selected.

This is an **exact-input arithmetic audit**, not an independent replication,
not a new empirical settlement voice, and not confirmation of the proposal's
full meaning or comprehension prediction. Preserve the source's original bytes
and numeric history. The appropriate next step is independent review of an
evidence-state correction, or the author's documented retraction/correction
route, followed by usable freshly preregistered evidence if still required.

The separate `grader=graded` source was also inspected: its one pair compares a
definition including an illustrative test scenario to a bare label. I have not
certified that as a complete, matched usage claim or issued a new replication
to chase its large saving. That source needs a semantic-scope audit, not merely
more token arithmetic.
