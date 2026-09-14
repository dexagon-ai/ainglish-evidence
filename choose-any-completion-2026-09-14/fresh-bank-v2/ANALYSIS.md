# Frozen candidate analysis — must be reviewed before inference

This specification is prospective and report-only. No observed target response informed it.
It cannot change the official comprehension carrier, its resolution rule, or the confirmed-loss
veto. A result may be adverse or inconclusive. Both forms must satisfy a claimed joint success;
pooling must not conceal a failing form. English's incumbent training/tokenizer advantage remains
part of the tested current-reader setting, not evidence about future Ainglish-trained readers.

## Fixed scope and outcomes

- 144 authored worlds, 72 assigned per form, six named domains; one form per world.
- Two fixed qualified reader configurations; SDK arm assignment by seed/reader/item. The two
  readers may receive the same arm for a world. There are 288 target calls, not 576 matched calls.
- Official scalar: the SDK's equally weighted two-form joint exact-answer accuracy difference,
  Ainglish minus careful English, percentage points. Preserve its interval, strata, calibration,
  yield/absence, per-member results and resolution unchanged. No new `replicates_hash` is attached.
- Supplementary tables: joint, policy-list and guarantee-list accuracy; every form/domain/policy
  decision; form/domain/reader/arm counts; choice positions; and actual misconception opportunities.
- A response outside the menu is joint incorrect but does not disclose policy/guarantee choices.
  List it as off-option and separately bound partial-error rates treating such unknowns first as
  all correct and then as all incorrect. Typed missing cells are not scored; retain denominators
  attempted/live/missing and the official guard outcome. Never repair or repeat a bad response.

## Preserve within five percentage points: conservative supplementary bound

For each form separately and each reader r, let k_A/n_A and k_E/n_E be live joint accuracies.
Compute a one-sided exact-binomial lower limit L_A at tail probability alpha/(2R), and upper
limit U_E at the same tail, with alpha=.05 and R=2. Combine with the *actual* within-form arm
denominator weights: L_delta = sum_r(n_A_r/N_A * L_A_r) -
sum_r(n_E_r/N_E * U_E_r). This is a conservative 95% lower bound for that fixed weighted contrast
under the within-reader binomial model. The union bound does not require independence between
readers or between arms. Missing an arm makes the bound unavailable, never a pass.

It DOES require independent exchangeable worlds within each reader/arm and stable arm assignment;
the authored common frames may violate those assumptions. Therefore label it **conditional on the
binomial-world model**, not a distribution-free or natural-population certificate. Use L_delta >
-0.05 to call that form conditionally non-inferior. The all-forms claim requires BOTH per-form
tests to pass (intersection-union decision); these are not advertised as a joint confidence region.
Report individual-reader lower differences too using the same component limits. Do not count two
responses on a shared world as two independent worlds in a pooled binomial interval.

This deliberately conservative method may not certify 5pp preservation even at perfect accuracy
in 144 worlds. Exact boundary diagnostics must show that BEFORE spend. The older optimistic normal
power reference describes a different assumed analysis and is not the power of this method.
Do not replace this method with the most favourable interval after seeing results.

The exact-binomial limits invert binomial tail probabilities; see the primary statistical
reference: https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm . At zero failures the
one-sided 95% error upper limit is 1 - .05**(1/n), not zero. At all successes the lower success
limit with tail a is a**(1/n). `report.py` verifies these boundary identities without inference.

## Correlation sensitivity, not a replacement success rule

Use 20,000 bootstrap draws, seed 2026091463. First resample world IDs WITHIN each form/domain,
keeping every observed reader cell of a selected world together. Separately resample the 12 frame
families as clusters, keeping all their cells together and recalculating the same fixed-form
contrast; record undefined draws and denominator changes. Publish 2.5/97.5 percentiles, plus a
leave-one-frame-family-out contrast range. Do not resample reader endpoints as if two represented
a model population. A ceiling [0,0] bootstrap remains a finite observed-data degeneracy, never a
preservation certificate. These sensitivities cannot eliminate the six-domain authored-sample
limitation and are never substituted for the SDK result or the bound above.

## Absolute accuracy and over-inference

Report the declared point targets/refuters separately: >=90% exact joint accuracy; <85% exact
accuracy; >5pp loss; >10% wrong-pole policy decisions in any domain; and >10% of readers inferring
unpromised equal odds for choose-any or crypto unpredictability/later independence for draw-uniform.
The 85–90% zone is not success. A point criterion and confidence-backed assertion are different.

For absolute accuracy/error proportions, give per-reader/per-form (and relevant domain/contrast)
exact-binomial 95% intervals with n=that reader's distinct offered worlds. For sparse or zero
opportunities, explicitly say unmeasured. Pooled counts are descriptive; no naive pooled-binomial
precision. On misconception opportunities an inclusion AND an exclusion must appear somewhere in
the menu. Report errors/known live offered cells, off-option unknowns, typed absences, and the
zero-error finite-sample upper bound. Tiny denominators cannot establish the absence of a problem.
The guarantee inference rates concern this fixed panel's responses, not a random sample of people
or AI systems. The campaign does not recruit expensive human panels or claim human validation.

## Decision and replication boundaries

Always publish official and supplementary results together, including inconvenient disagreement.
No untested bare-random claim, no generic superiority inferred from a tie, no future-training
benefit inferred from present cost. A later fresh-input replication has its own principal, worlds,
manifest and outcome; it preserves the finalized contract. An instrument review is not a study
replication. Ballot voters retain independent judgment under unchanged current rules.
