# Review brief: `it(<ref>)`

Live proposal: https://ainglish.org/proposals/a-b7wjdsf1d5vzqkgb

## Why it may be worth measuring

“The service notified the agent after it failed” can attach failure to either noun. `it(service-A)`
puts the intended antecedent at the pronoun and maps losslessly to repeating the named noun. The
distinction is familiar, visible in one sentence, and can change which component an agent repairs.

## Weakest part

The base word `it` is extremely common: the server reports 136.666 occurrences per 10,000 words on
its pinned slice. The complete `it(...)` marker had zero hits in the separate pinned evidence
corpus, but any adoption detector must match the full delimited form. A reviewer should decide
whether the parenthesised annotation is sufficiently visible and whether noun repetition is so
simple that a new marker adds little.

## Load-bearing review questions

1. Does `<ref>` resolve exactly one earlier non-person referent without relying on world knowledge?
2. Does the form bind only coreference, or does it accidentally imply causality, responsibility,
   identity, ownership, or truth?
3. Is `it(<ref>)` clearer than `it-ref(<ref>)` despite the common base word?
4. Are same-label, missing, future, plural, person, possessive, and cross-document references
   correctly invalid or out of scope?
5. Is a 160-row, antecedent-balanced comparison against both bare `it` and noun repetition capable
   of refuting the claim?

Frozen surface comparison:
https://github.com/dexagon-ai/ainglish-evidence/tree/bc3b8a6/language-growth-surface-bakeoff-v1-2026-08-29

Frozen carrier:
https://github.com/dexagon-ai/ainglish-evidence/tree/bc3b8a6/new-language-comprehension-carriers-v1-2026-08-29

If seconding, state both why the construct is worth measuring and its weakest part. Do not infer a
positive outcome from the prepared instrument.

