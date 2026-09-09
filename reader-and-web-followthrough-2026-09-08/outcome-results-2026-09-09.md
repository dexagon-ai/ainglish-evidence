# Mean outcome / likeliest outcome: five-study result

Completed **9 September 2026**. **The programme does not qualify this version for
ratification or flagship claims.** All five prespecified studies were filed; none
is independently confirmed. One diagnostic has an adverse interval. The primary
joint task performs poorly in both languages, so it also exposes a task/reader
resolution problem rather than cleanly isolating an Ainglish-specific failure.

## What ran and what was preserved

The [prospective plan](outcome-analysis-plan.md), five answer-bearing packets and
their exact author semantic review were frozen before target calls. Both full
cost prerequisites were independently confirmed within the +6 allowance at each
fresh pre-run check. Two cached qualified reader families were used: the declared
Mistral Small 3.2 24B and Gemma 3 12B Q4 opaque-choice instruments, with identical
definition exposure in the two arms. No models were downloaded.

There were **752 target items, 1,504 target calls and 240 calibration calls**:
1,744 recorded calls in total, no retries or transport faults. The five studies
share authored worlds/templates and are not five independent replications.
`analyze_outcome.py` replays every cell allocation, original key, score, manifest
commitment, stratum estimate and attested item-bootstrap interval without model
calls. All five replays pass. Every raw journal, cell result and receipt is kept
in the respective `execution/` directory.

## Official results, kept separate

These are the filed stratum-weighted accuracies, not pooled raw-cell percentages.
Differences are Ainglish minus English, in percentage points. The intervals are
the official 95% item-bootstrap intervals, without correction for repeated
templates or multiple comparisons.

| Study | English | Ainglish | Difference [95% interval] | Current interpretation |
| --- | ---: | ---: | --- | --- |
| [Primary, careful English](https://ainglish.org/measurements/cba951d749ea72d39703a3703e6c966962fb6890f3ed006970a15df21a781e05) | 11.67% | 9.18% | −2.495 [−7.6292, +2.6829] | Strata unresolved; mean form at floor |
| [Primary, compact technical English](https://ainglish.org/measurements/785d96761cf4156530c91c7feabca6fe9778de4c8f11861372e0420367e7d22a) | 12.59% | 9.89% | −2.705 [−8.2810, +3.2113] | Strata unresolved; mean form at floor |
| [Majority/certification, careful English](https://ainglish.org/measurements/fdffbc61a7c411ace219500c141321f535466996bb6f8abb57f487ac96379163) | 70.14% | 76.60% | +6.450 [−3.9275, +16.8002] | Inconclusive |
| [Majority/certification, compact English](https://ainglish.org/measurements/8b3b90535e0f2422353e7e058d2a0b0118433df34459a348b45b0b06f064c5a5) | 80.07% | 66.99% | −13.075 [−22.6963, −2.9569] | Adverse, not independently confirmed |
| [Specification sufficiency](https://ainglish.org/measurements/031ef2276aca94b619fb876bfbfd77a75e394bf245c7cd501761d343304d66c7) | 78.50% | 73.96% | −4.535 [−23.6275, +14.8313] | Inconclusive |

The higher majority-careful score is not a substitute for the primary task or its
stronger-comparator result. None of these aggregate lower bounds clears the
declared −3pp noninferiority margin. This is not converted into a pass by being
non-significant against zero.

## Check both forms, not just the aggregate

Primary stratum-weighted Ainglish accuracies were:

| Form | Careful comparator | Compact comparator |
| --- | ---: | ---: |
| mean-outcome | 4.80% | 7.96% |
| likeliest-outcome | 13.56% | 11.81% |

All are below the predicted 90% exact interpretation target and the 85% adverse
signal. This is a four-bit **joint** task, not a direct estimate of how many
humans understand a short example. Its equal-choice chance rate is 6.25%, but its
most frequent correct complete answer is 50%; therefore “above random chance”
would be an especially misleading success claim here.

The per-bit diagnostics also matter. On the primary careful arm, Ainglish got
claim truth right in 119/243 cells, support membership in 92/243, unique-mode
status in 170/243 and the supplied no-guarantee condition in 243/243. These are
not merely near-perfect component answers penalised by a joint score. English
also failed substantially: 128/237, 100/237, 162/237 and 237/237 respectively.
All form/domain/boundary/variant/reader counts are retained in `analysis.json`.

One compact mean-form difference has a descriptive lower bound just above −3pp,
but its Ainglish absolute accuracy is 7.96% and its resolution is floor-bound.
That cannot rescue the claim. The compact majority diagnostic is adverse on both
forms by point estimate; the per-form intervals and the reader split are also
retained, not pooled away.

## Safety probes and their limits

There were zero false-guarantee endorsements in either primary study, and zero
false-model-certification endorsements in the majority supplements. Every such
gold is “no” and every cell includes a caution against those inferences. Thus
these results establish behaviour on the caveated frozen examples, not general
discrimination of guarantees/certification. Nominal cell-Wilson intervals are
included for descriptive completeness and expressly cannot certify a broader
threshold under shared templates/items/readers.

The majority supplements have an 80% constant-answer baseline, and the
specification supplement a 75% constant-rejection baseline. Specification errors
were false acceptance of insufficient models: English 7/33, Ainglish 8/31. No
false rejection of a sufficient specification appeared. Neither comparison earns
a broad scope-comprehension claim.

## What should happen next

1. The author and reviewers should inspect these results and the retained cells,
   especially the failed mathematical/interpretive components and the stronger
   comparator. The requested semantic review was real and its limits were kept;
   it was not experimental confirmation.
2. If the instrument/task remains scientifically suitable, a different eligible
   principal can independently test the adverse result on genuinely fresh inputs
   with the source's declared population and estimator. Another reader population
   is a new original, not a silent substitution. Numerical reproduction alone is
   not independent confirmation.
3. If the task fails to isolate the intended linguistic distinction, identify the
   specific defect publicly and prepare a prospective successor study, retaining
   these null/adverse records. No post-result key edits, target exclusions or
   repeated attempts for a preferred sign.
4. A justified author revision or retirement of this version is a legitimate
   progression outcome. The distinction itself need not be declared permanently
   unsuitable: today's English-trained readers do not test future trained-weight
   or tokenizer benefits. That future possibility is also not present evidence.

Live after filing: the missing-comprehension-original action has become a request
for independent replication. There is **no new ratification**, and token
prerequisite completion does not establish the unreadiness away.
