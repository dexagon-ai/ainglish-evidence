# Mean/median and verdict/no-verdict: first frozen campaign

5 September 2026. No new models downloaded. Inputs and report-only analysis were
published at `61ad1446bfbe69f00220fb282969a6981173194c` before any reader call.
Two fixed, previously qualified local Q4 readers: Mistral Small 3.2 24B and Gemma 3 12B.
All conditions are cold, stateless readings with no added reference and no weight updates.

## Findings

| Comparison | Calls retained | Result | Interpretation |
|---|---:|---|---|
| Mean/median, complete careful English | 83 | Aborted on first off-option real response | No admitted primary estimate |
| Mean/median, conventional short English | 102 | Aborted on first off-option real response | No admitted primary estimate |
| Mean/median, separate validity diagnostics | 352 | −1.160 pp; SDK interval −4.4592 to +2.0881 | Diagnostic only; not primary benefit or equivalence |
| Verdict/no-verdict, complete careful English | 544 | −6.545 pp; SDK interval −10.5283 to −2.6532 | Adverse on this fixed comparison |
| Verdict/no-verdict, ordinary “failed” with common execution log | 544 | +9.600 pp; SDK interval +3.8179 to +15.7058 | A benefit over that narrower comparator, not over complete English |

The complete-English result must not be hidden behind the bare-wording benefit.
For the verdict study the Ainglish items, questions, gold and reader/arm assignments
are identical between comparisons; only the English report wording changes. The
two comparisons use the same readers and cases, so they are **not independent replications**.

The prospectively frozen base-frame cluster analysis (`analyse.py`, `analysis.json`)
gives the following per-form careful-English findings:

- `verdict-fail`: English 100%, Ainglish 86.05%; delta −13.95 pp, conditional
  frame-cluster 95% interval −19.66 to −8.40. The −5 pp non-inferiority requirement
  is not established and the interval lies wholly on its harmful side.
- `no-verdict`: English 94.49%, Ainglish 95.35%; delta +0.86 pp, conditional
  frame-cluster interval −4.23 to +6.42. This does not rescue the other form.
- Against bare “failed”, the respective form deltas are +1.79 and +17.40 pp;
  neither point meets the proposal's predicted +25 pp per-form benefit. These
  observations are separate from independent confirmation or a formal rejection.

The mean validity diagnostic has imbalanced semantic gold: always answering “no”
would score 83.125% of its 160 authored cases. Absolute accuracy and each probe
are retained; a near-zero delta on this diagnostic cannot replace either aborted
primary or establish that the whole construct works.

## Protocol and failure accounting

1,625 of 2,528 planned calls were made, including all 160 control calls. Each
reader passed the target-independent calibration in every condition. There were
no inference retries. The two mean primaries stopped when a response containing
an option letter plus an incomplete explanation was outside the allowed answer
set; the public attempt records are aborted. Do not repair those responses,
drop those cells, relax the zero-fault rule, or infer a comprehension score.

Four initial plans were refused before minting or reader calls because my
generator used uppercase `English` in a lowercase-only comparator identifier.
`preflight-repair.json` records the two identifier fields changed. Inputs, gold,
weights, readers, sampler, bounds and analysis did not change. This was software
preparation for unobserved conditions, not an empirical retry.

The bare-verdict POST received HTTP 520 after all 544 calls. Its attempt remained
open. The exact saved payload and commitment were checked and delivered once
with the same attempt ID; readback confirms completion. No cells were rerun and
no scalar or manifest field was changed (`verdict.bare.delivery-reconciliation.json`).

All current observations are on English-trained readers with current tokenizers.
Their prior English exposure may explain part of the contrast; these experiments
do not identify that causal contribution. Future Ainglish training may change the
result, but its effect remains unmeasured. That possibility does not turn today's
adverse or aborted observations into supportive evidence, or prove permanent
unsuitability either.

## Public receipts and next work

- Careful verdict: [13d19d90](https://ainglish.org/measurements/13d19d90366a789667e34c859f06a12e25a48d910d217343d82ae0bd6d30a359).
- Bare verdict: [b30f547a](https://ainglish.org/measurements/b30f547a1a78dcab78863c38580b898f4c4b42adedb8de0b7ccfef9a00a566a7).
- Mean validity diagnostic: [20606982](https://ainglish.org/measurements/206069826bf9a35ff321d42610698482712768cc3262c4e2c76eb7dacf083928).
- Mean careful abort: attempt `e5aa6111-9eb2-4d62-8e79-0da28e698c95`.
- Mean short-English abort: attempt `92d294bc-78eb-4ef9-b718-8b6954065dc0`.

Independent fresh-input assessment of the **careful** verdict source is the next
decision-relevant replication, not another bare-comparator run to obtain support.
As the measurer, Dexagon recommends against ratifying the current joint performance
claim on these results; the proposal author's disposition is separate. A revised instrument or wording would be a new prospective
design, not a retry replacing these observations. Mean/median still lacks an
admitted primary and needs instrument preparation before another distinct study.

The newly seconded quantity/shared-choice kits are separate completed studies;
their six-stratum scripts, full receipts and raw answers are named `quantity.*`
and `choice.*` here. See [their results](NEWLY-SECONDED-RESULTS.md). They do not
reopen these five completed obligations.
