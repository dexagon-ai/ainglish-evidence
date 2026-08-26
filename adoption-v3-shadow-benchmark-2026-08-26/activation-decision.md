# Adoption detector v3 activation decision

Decision at 2026-08-26: **do not activate; keep v3 shadow-only**.

This decision evaluates the proposed detector against the frozen artifacts in this directory. It
does not treat model agreement as human ground truth, does not turn abstention into non-use, and
does not claim that a no-write shadow run demonstrates a zero write-side blast radius.

| Gate | Observation | Decision |
|---|---|---|
| Frozen population and detector | 2,901 messages and 35 ratified proposals are digest-pinned; the corrected detector digest is recorded. | Pass for diagnostic reproducibility. |
| Adversarial fixtures | 28/28 expected labels. | Pass on the declared fixture set only. |
| Exhaustive disagreement accounting | All 36 corrected v2/v3 disagreement rows are retained. | Pass for enumeration. |
| False-negative review | Two local readers agree on 30 rows and disagree on six; the first pass missed 29 standalone claim tags. | Fail for activation: model triage is not ground truth and six rows remain unresolved. |
| Untouched holdout | The frozen corpus was inspected to repair the claim-tag rule. | Fail: the corrected detector has no fresh, untouched holdout result. |
| Abstention accounting | v3 exposes abstentions, but production storage has not demonstrated an uncertainty-preserving observation path. | Fail until abstention is stored separately and cannot become observed zero use. |
| Prompt-injection and mixed-language robustness | No dedicated frozen attack suite or multilingual false-negative bound is present. | Fail. |
| Repeatability | Exact prompts and model digests are retained, but stochastic local readers do not define the detector verdict. | Informative, not an activation gate. |
| Write-side blast radius | Shadow mode does not write observations. | Not measured. Zero writes in a no-write process is tautological, not evidence for activated behavior. |

## What would reverse the decision

1. Freeze a new corpus window after the corrected rule, without inspecting labels while freezing.
2. Independently adjudicate every v2/v3 disagreement and a sample of agreements and abstentions.
3. Add frozen prompt-injection, mixed-use, code, quotation, fragment, and multilingual cases.
4. Demonstrate that abstention is persisted as detector uncertainty and never converted to zero use.
5. Run an isolated write-capable dry run against a disposable observation ledger, then calculate
   `unclaimed_verdict_flips` over a preregistered affected population.
6. Put activation, version change, and deprecation consequences in a separately reviewed change.

Until those conditions hold, the useful result is an adverse diagnostic: v3 found meaningful
mention/use distinctions and also exposed a false-negative class during development. It is ready
for more measurement, not production authority.
