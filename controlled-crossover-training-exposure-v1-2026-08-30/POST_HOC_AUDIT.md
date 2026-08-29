# Post-hoc paired audit

Status: **complete**

This deterministic, inference-free audit checks the frozen 2,592 predictions. It does not rerun a model or replace the prospective interpretation.

## Paired cold cross-over

| Construct | Exposed / 48 | Unexposed / 48 | Difference | Exposed-only / unexposed-only | Exact paired probability | Prospective interpretation |
|---|---:|---:|---:|---:|---:|---|
| among-others / and-no-others — is the list the whole list? | 48 | 24 | +0.500 | 24 / 0 | 1.1920929e-07 | `broad_behavior_shift` |
| they-one / they-many — say whether ‘they’ is one actor or several | 48 | 48 | +0.000 | 0 / 0 | 1 | `broad_behavior_shift` |
| observed / reported(<by>) / inferred(<from>) - mark where a claim came from | 48 | 30 | +0.375 | 18 / 0 | 7.6293945e-06 | `broad_behavior_shift` |
| one-or-more(<role>) / exactly-one(<role>) — does ‘a reviewer’ require at least one participant or exactly one? | 48 | 45 | +0.062 | 3 / 0 | 0.25 | `broad_behavior_shift` |
| repeat-event / restore-state — did ‘again’ repeat the action, or only bring the result back? | 48 | 34 | +0.292 | 14 / 0 | 0.00012207031 | `selective_uptake` |
| attempt: / ensure: — say whether the instruction tolerates failure | 48 | 36 | +0.250 | 12 / 0 | 0.00048828125 | `selective_uptake` |

The exact paired probabilities are post-hoc descriptive diagnostics over the 48 synthetic held-out frames. They are unadjusted for six comparisons and are not population-level inference.

## Strict-output validity

| Condition | Valid | Invalid | Validity |
|---|---:|---:|---:|
| `base` | 460 | 404 | 53.2% |
| `adapter-a` | 864 | 0 | 100.0% |
| `adapter-b` | 864 | 0 | 100.0% |

All 404 malformed outputs came from the untouched base. The adapters learned the terse one-key JSON response format while learning their assigned tasks. Therefore absolute base-versus-adapter accuracy conflates semantic performance with instruction and length compliance. The adapter-versus-adapter paired comparison is the cleaner selectivity diagnostic.

## Interpretation

- Event-versus-state recurrence and failure contract pass the frozen selective-uptake rule and retain sizeable paired cross-over advantages.
- List completeness and claim source have large exposure-specific cold advantages, but fail frozen safety gates because behavior on bare ambiguity worsened; they remain broad behavior shifts.
- Pronoun number is perfect under both adapters, so this experiment cannot attribute its improvement specifically to pronoun exposure.
- Role cardinality differs by only 3 of 48 paired frames; the post-hoc exact paired probability is 0.25 and its frozen classification remains broad behavior shift.
- Every exposed cold construct scored 48/48, with no pole or opaque-label collapse. That demonstrates held-out task acquisition under this high-dose supervised setup, not future-pretraining performance.

## Provenance-label note

The raw result field named `public_preregistration_commit` contains `5345b2dabf0e0b2761b737d28e75eea4f2a33469`: the latest public commit touching the study directory when evaluation began. The actual corpus/protocol freeze is `d33efd29259718c4ede811e062a24fd36d8b56b5`, and the adapter-receipt freeze is `5345b2dabf0e0b2761b737d28e75eea4f2a33469`. Both stages and every input digest remain independently bound; this is a field-label ambiguity, not input drift. Raw receipts are retained unchanged.

## Claim boundary

This is a project-linked supervised QLoRA development result. It is not foundation-model pretraining, tokenizer integration, human validation, independent Ainglish evidence, a ratification recommendation, or proof of future efficiency.
