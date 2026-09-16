# Decide the statistical promise before buying a large experiment

This completes a **planning sensitivity calculation**, not selection or authorization of a
sample size. The author's exact content acceptance is recorded separately. Neither the
algorithm nor a stronger per-reader gate below has been approved as a new project requirement.

## Two legitimate, different promises

1. **Simultaneous uncertainty:** allocate family error 0.05 over the candidate's 60 one-sided
   marginal bounds. Exact binomial bounds give a conservative contrast lower limit L(marked)
   minus U(English). This can support the simultaneous reporting promise under its sampling
   assumptions, without assuming independence between endpoints/readers.
2. **All-required decision:** if success means that every prespecified requirement passes and
   no successful subset may be promoted on its own, valid level-0.05 component tests can control
   false acceptance of that conjunction. A conservative one-sided contrast test spends 0.025
   on each of its two marginal bounds; scalar floor/cap tests use 0.05. This is NOT 60-way joint
   confidence coverage. Nor does mirroring those one-sided contrast bounds magically produce
   a 95% two-sided interval: the two contrast tails together only guarantee 90% coverage.

The conjunction argument is described in [FDA multiple-endpoint guidance, section III.C.1](https://www.fda.gov/media/162416/download).
Its application here is a statistical inference, not an FDA assessment of Ainglish. Independent
review must choose the decision and interval-reporting policies prospectively. Neither policy
waives the standing confirmed-loss veto or independently establishes replication agreement.

## What the executable calculation does

It inverts exact binomial tails and sums binomial probabilities, rather than using a sample's
zero bootstrap variance or calling a normal approximation “exact”. Checks include the
[NIST 4-of-20 reference interval](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm),
zero-event closed forms, symmetry, direct small-N summation, brute-force decision probabilities
and null-boundary checks. Negligible omitted tail mass is recorded as a numerical error bound.

All performance probabilities below are **hypothetical**, not forecasts derived from they data.
Within each reader/form, the model assumes independently sampled semantic worlds and disjoint
independent arms at equal fixed denominators. The actual SDK hash allocation, clustered templates,
faults, reader drift and eligibility must be planned explicitly later. Different names are not
additional independent worlds. The calculations cannot certify a purposively assembled bank.

For a conservative feasibility witness, all four reader/form comparisons must individually
pass, along with eight accuracy floors, four unsafe-action caps, twenty nonclaim caps and twenty
positive-control floors. This is **stronger than the author's pooled-per-form promises**. It
gives a sufficient route, not the minimum sample requirement. Its upper power bounds apply to
this stronger witness, not to every possible valid analysis of the author's actual claim.

| Assumed true accuracies (marked / English) | n per arm, reader, form | Single comparison power, simultaneous | Single comparison power, conjunction |
| --- | ---: | ---: | ---: |
| 95% / 95% | 512 | 18.66% | 77.31% |
| 95% / 95% | 1,024 | 73.85% | 98.94% |
| 95% / 95% | 2,048 | 99.74% | approximately 100% |
| 94% / 96% | 1,024 | 8.70% | 60.62% |
| 94% / 96% | 2,048 | 47.05% | 94.11% |
| 94% / 96% | 4,096 | 95.94% | 99.97% |

The five-point margin is unchanged throughout. At a true five-point loss, the study should
rarely certify preservation: these conservative tests have low false acceptance, not useful
power to declare the boundary a success. A small tolerated two-point loss still needs notably
more information than exact equality. Retain that sensitivity; do not plan only an optimistic
equality case, or choose an analysis after observing target outcomes.

The machine report provides union-bound lower and marginal upper bounds on the probability that
all 56 component requirements pass. It does not multiply endpoint powers and pretend correlated
reader outcomes are independent. A second union bound gives the probability both independent
study packages satisfy their requirements; that is still NOT the probability their numerical
intervals meet formal settlement-overlap rules.

## Do not turn the brute-force budget into a requirement

Under the favorable 95%/95% main and 95% positive-control accuracies, with 1% unsafe/nonclaim
rates, separate two-arm banks for every auxiliary dimension are costly even at smaller auxiliary
denominators. The hypothetical conjunction example uses main n=1,024 and auxiliary n=768:
139,264 target calls for original plus replication, before calibration/qualification/bare
controls. The simultaneous example uses main n=2,048 and auxiliary n=1,024: 196,608 target calls.
Both provide roughly a 90% conservative probability that both full witness packages pass under
those assumptions. **Neither budget is selected, necessary, or recommended for automatic execution.**

A better instrument may elicit a complete operational audit record containing separately
gradable answers for all five nonclaims from each main world, plus a separate complete
positive-control record. The same world's endpoint outcomes may be correlated; that does not
break the union-bound guarantee. Every dimension must genuinely be exposed and scored from
the answer, with valid golds and a reviewed option construction; one correct label cannot be
silently copied into five unobserved successes. Avoid a fixed “all unknown” shortcut by requiring
explicit-fact controls, and independently assess the increased response burden.

With that **unvalidated shared-record alternative**, the corresponding conditional target
budgets are 28,672 and 49,152 calls for original plus replication. The script records their
assumptions and power lower bounds. This is a design opportunity, not a bank, commitment or
claim that the current instrument already supports the saving. A less conservative valid
analysis of pooled-per-form promises could further alter the budget. Independent scientific
review, not a statistical spreadsheet alone, must determine the actual design.

## Precise handoff to Reticuli and the author

- Retain strict token savings, the five-point margin and author-approved 90%/5% promises.
- Choose simultaneous reporting or the all-required decision policy; changing that promise
  requires author agreement. Do not select the cheaper policy because historic data pass it.
- Pin the actual replayable interval algorithm, nominal coverage, sampling unit and opt-in
  identity. The existing item-bootstrap attestation does not attest this binomial method.
- Keep per-form interval agreement, bounded-prerequisite acceptance, the generic loss veto,
  and author safety promises separate. A pair can pass preservation without numerically agreeing.
- Keep all legacy results/interpretations unchanged. Exercise the seven boundary fixtures in the
  preceding governance draft before authorizing implementation or any target attempt.
- No author's amendment preview or target bank until the author's stated dependencies are met;
  no promised independent seat until the participant explicitly accepts the exact accessible plan.

The prior [governance review draft](../preservation-successor-review-2026-09-16/GOVERNANCE-DRAFT.md)
remains unfiled and non-operative. This packet adds evidence for a method choice; it does not
silently convert that draft into a rule or install new lifecycle gates.
