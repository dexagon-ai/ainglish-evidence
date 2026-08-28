# Analysis encoding erratum

The frozen run completed all 264 planned observations. The first invocation of `analyse.py` then
refused before creating `analysis.json` because 24 clarification repairs returned malformed or
out-of-contract JSON. The runner truthfully stored each as an explicit `{"decision":"invalid"}`
repair. The benchmark's older `classify_rows` contract permits only an `act` repair or `null`, even
though its reference Ollama runner maps a non-action repair to `null` plus a parse error.

This is an encoding mismatch, not a missing model outcome and not permission to retry. The raw
`results/responses.jsonl` is immutable. `analyse_recovered.py` creates a scoring-only view in which:

1. only a repair whose stored decision is `invalid` is mapped to `null`;
2. the first decision, raw malformed repair, parse error, item, arm, track, model condition, and all
   usage fields remain in the immutable source result;
3. zero-repair and final-success classifications cannot improve through the mapping, because no
   invalid repair was a valid action; and
4. the standard scorer's token summaries are explicitly marked unsuitable, because it omits token
   usage for a `null` repair. Complete raw interaction-token summaries include those 24 calls
   separately in the recovered analysis.

All 24 cases occur in matched base/adapter cell locations: 12 per condition. This symmetry is
reported but is not used to excuse the defect or manufacture a token claim. The recovery script and
erratum are post-result additions and are not represented as preregistered files.
