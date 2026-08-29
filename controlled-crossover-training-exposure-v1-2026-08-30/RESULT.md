# Controlled cross-over training-exposure result

Status: **complete**

All 2592 planned predictions completed. Invalid predictions: **404**. No model was downloaded and no inference was retried.

Response digest: `8b55b92e4cfb7a41db500636d087c0a8ab81065601e9cda04f5bf88f63df3c95`. Analysis digest: `14b7b279ec179ecb15aec936f05d3c2fa9c6149ba9b4a6f761fcde9c52ea04ce`.

## Overall arms

| Condition | Cold Ainglish | Careful English | Bare ambiguity |
|---|---:|---:|---:|
| `base` | 26.4% | 44.4% | 14.9% |
| `adapter-a` | 89.9% | 94.8% | 0.0% |
| `adapter-b` | 85.4% | 96.9% | 28.1% |

## Construct-level cross-over result

| Construct | Exposed | Base cold | Exposed cold | Unexposed cold | Exposed-base | Exposed-unexposed | Careful change | Bare change | Interpretation |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| among-others / and-no-others — is the list the whole list? | `adapter-a` | 10.4% | 100.0% | 50.0% | +0.896 | +0.500 | +0.750 | -0.271 | `broad_behavior_shift` |
| they-one / they-many — say whether ‘they’ is one actor or several | `adapter-a` | 64.6% | 100.0% | 100.0% | +0.354 | +0.000 | +0.583 | -0.083 | `broad_behavior_shift` |
| observed / reported(<by>) / inferred(<from>) - mark where a claim came from | `adapter-a` | 0.0% | 100.0% | 62.5% | +1.000 | +0.375 | +0.188 | -0.396 | `broad_behavior_shift` |
| one-or-more(<role>) / exactly-one(<role>) — does ‘a reviewer’ require at least one participant or exactly one? | `adapter-b` | 14.6% | 100.0% | 93.8% | +0.854 | +0.062 | +0.896 | -0.146 | `broad_behavior_shift` |
| repeat-event / restore-state — did ‘again’ repeat the action, or only bring the result back? | `adapter-b` | 31.2% | 100.0% | 70.8% | +0.688 | +0.292 | +0.396 | +0.000 | `selective_uptake` |
| attempt: / ensure: — say whether the instruction tolerates failure | `adapter-b` | 37.5% | 100.0% | 75.0% | +0.625 | +0.250 | +0.333 | +0.104 | `selective_uptake` |

## Claim boundary

This experiment tests selective learnability under supervised QLoRA exposure. It is not foundation-model pretraining, tokenizer redesign, human validation, an independent Ainglish measurement, or a ratification recommendation.

A favourable exposed-versus-cross-over contrast would support only the narrow claim that the exact construct can be learned under this task and dose. A null or broad shift is retained without tuning or retraining.

## Post-hoc audit note

All 404 schema-invalid outputs came from the untouched base, whereas both adapters had perfect
strict-output validity. Absolute base-versus-adapter gains therefore partly conflate semantic task
performance with acquisition of the terse JSON response format. The paired adapter-versus-adapter
contrasts are the cleaner diagnostic of construct-specific uptake.

The deterministic [post-hoc paired audit](POST_HOC_AUDIT.md) reports those contrasts, verifies that
the exposed cold results did not collapse by pole or opaque answer label, and records a provenance
field-label ambiguity without modifying any raw receipt. This note and that audit were added after
the frozen primary analysis and do not replace its prospective classifications.
