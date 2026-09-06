# The first cross-family screen: no language cases were run

All three cached readers failed the original compound output screen. Each saw
16 neutral package records, not Ainglish language cases. The frozen rule required
at least 14 correct five-field answers, no truncation and one bare JSON object.

| Reader | Original declared score | Decision |
|---|---:|---|
| Qwen2.5 7B | 11/16 | Stop before language cases |
| Gemma3 12B | 0/16 | Stop before language cases |
| Mistral Small 3.2 24B | 0/16 | Stop before language cases |

These are **not** scores of Ainglish comprehension. Gemma and Mistral placed
otherwise correct answers inside JSON code fences. A later, explicitly post-hoc
audit that accepts one fence parses all 16 answers from each reader and finds
16/16 neutral meanings correct for those two models. Qwen remains 11/16, with
four sealed/open errors and one fragility error.

That diagnosis does not change the original decisions. No language targets are
retroactively authorised. A [separate successor](../cached-reader-semantic-2026-09-07/PLAN.json)
declared a single-fence protocol prospectively and used newly authored neutral
controls. The [audit code and cell results](../cached-reader-semantic-2026-09-07/QUALIFICATION-AUDIT.json)
retain both views with no effect on the earlier gate.

The models ran CPU-only through the existing shared service, one at a time,
without downloads. Mistral began only after a pre-load RAM stop was resolved;
it had not yet seen any control or target in this study. The exact continuation
and its source freeze are retained alongside the raw responses. No shared
service setting, unrelated workload or model file was changed.

The inference budgets, CPU options and model digests are in `PLAN.json`.
Provider-reported prompt/output counts are retained, but this transport did
not expose generated token IDs. This is not an exact output-ID recount, a
governance measurement or a comparison of trained versus untrained Ainglish.
