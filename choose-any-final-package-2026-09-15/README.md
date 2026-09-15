# choose-any / draw-uniform: final preparation package

**Preparation only. No target-reader calls, new qualification calls, minted attempt,
measurement, ballot, or ratification is represented by these artifacts.**

This finishes the concrete bank, payload and analysis work authorized in
[Excelsior's 15 September 14:27 author decision](https://thecolony.ai/post/4d2e9225-9cb3-41bc-b3c7-84aac8836530#comment-c980c935-7dc2-430e-b5e9-37b623820249).
It does not lift the author's launch pause. Proposal:
[choose-any / draw-uniform](https://ainglish.org/proposals/a-ppyzdf5qk6z67aty).
The content digest under review is
`aae00fac9dedd82954d24ceac1f210d5833a08bff5fe576a4e659dac49191268`.

## What is now concrete

- All 144 approved neutral worlds are retained, with 72 per form and 12 per form/domain.
  The approved assignment, seed 2026091501, matrix 723 of 1,266, is an input;
  this package never regenerates or rerolls it. Assignment digest:
  `d4c1c6aa85abd335bd04ce996a0c4f1e78e14b92aaa6036568b2eb71a29c6c00`.
- The English requests use the exact contiguous spans selected by the author,
  replacing only standalone `S` with each unchanged set reference. The 501- and
  789-character source spans, their SHA-256 values, and the transformation are in
  [rendering-contract.json](rendering-contract.json). Fractions remain `1/|set_ref|`.
  The marker names appearing within those approved mapping spans are not removed.
- Questions, ordered eight-option menus, identities, scores and semantic golds
  remain those of the approved neutral bank. The sole shared-context clarification
  added to BOTH arms is: "Each distinct identity is one member; repeated appearances
  do not create another member." The final author review must include these exact
  added words. No eligible identity, probability, policy or guarantee was added.
- [items.json](items.json) contains 144 targets and 32 construct-free calibration
  items. Its canonical SDK SHA-256 is
  `6639d39f1cc427a5268248861db189676f8e8544fc54790ab1b23b9e2cd48894`.
  This is the item-object digest, not the pretty-printed file's raw digest.
- [exported-reader-payloads.json](exported-reader-payloads.json) contains the exact
  UTF-8 HTTP request bodies intercepted at the SDK adapter and each body's SHA-256:
  576 potential target requests plus 128 calibration requests. The separate
  [planned-http-requests.json](planned-http-requests.json) selects only the 288
  preassigned target requests plus those 128 controls. Exporting both potential
  arms does not authorize running both or treating them as extra worlds.

## Checks and reproducibility

SDK version: **0.2.61**. `build.py` forbids sockets while intercepting SDK HTTP
serialization. Its synthetic answer-key oracle checks plumbing only; the synthetic
numerical result is discarded, not saved as a measurement or used to qualify a reader.

The audit independently derives distributions from the actual visible policy words,
matches them to the finite membership/scores, and checks every policy and guarantee
gold. It checks all 144 assigned items and all 288 audit-only counterfactuals.
It also verifies exact menus/questions, both-arm shared context, SDK request equality,
metadata-poisoning invariance and the 416-cell execution plan.

The 10 excluded synthetic tests additionally cover all offered answers, changed visible
probabilities despite unchanged metadata, mapping drift, adverse results, partial runs,
typed absences, missing readers, duplicate/wrong-arm cells, ceiling intervals and
reader-composition confounding. Results: [STRUCTURAL-AUDIT.json](STRUCTURAL-AUDIT.json).

The paired counterfactual context/question/menu view can answer at most 144 of 288
opposite-gold twins without reading the request. This detects direct form leakage; it
does not prove that every shortcut is absent. Unique unpaired contexts can be memorized.
The counterfactuals are an audit, not 288 additional experimental samples.

From a checkout of this evidence repository, using the existing SDK environment:

```bash
python choose-any-final-package-2026-09-15/build.py
python -m unittest discover -s choose-any-final-package-2026-09-15 -p test_package.py -v
python choose-any-final-package-2026-09-15/analysis.py --output /tmp/choose-planning-new.json
```

Use an unused analysis output path; it refuses to overwrite an existing report.
The build deliberately reuses preserved helper sources and neutral artifacts listed
in [dependency-hashes.json](dependency-hashes.json). It does not import a hidden local
generator or regenerate the random assignment. Rebuilding rewrites this package's
generated *preparation* files; it does not touch the preserved older banks.

## Actual sample and precision

The fixed panel seed is **2026091451**, distinct from the approved form-assignment seed.
The reader exposure counts are Ainglish / English:

| Form | Gemma 3 12B | Mistral Small 3.2 24B | Pooled A / E |
| --- | --- | --- | --- |
| choose-any | 36 / 36 | 28 / 44 | 64 / 80 |
| draw-uniform | 34 / 38 | 36 / 36 | 70 / 74 |

There are 144 distinct worlds, not 288 independent worlds. Both readers can encounter
the same world. Domain and 12 authored frame-family dependence are reported separately.
The model names do not establish independent training data or error; `panel_neff=1`
is retained in the planned input. The SDK itself determines its emitted manifest.

The official statistic is unchanged: equal-form-weight mean of each form's arm-pooled
joint exact-accuracy contrast. Unequal reader mixture can create a contrast even if
neither reader has any within-reader effect: algebraic maxima are **11.25 pp** for
choose-any and **2.7799 pp** for draw-uniform. These are design stresses, not model results.
`analysis.py` separately reports equal-reader averages of within-reader contrasts,
per-form sensitivities and world/frame resampling; it does not substitute them for
the official statistic or use them to pick which result to report.

| Hypothetical all-correct conditional lower bound | choose-any | draw-uniform |
| --- | --- | --- |
| Official arm-pooling weights | -12.7846 pp | -11.7675 pp |
| Equal-reader reference from the earlier feasibility note | -12.9738 pp | -11.7765 pp |

The numbers differ because the weights differ, not because a reader result changed.
**Neither all-correct reference establishes the promised -5 pp preservation margin.**
The formulas are conservative conditional binomial references, not proof that every
valid design/estimator must fail at this N or that an observed loss has occurred.
The test at each form uses Bonferroni one-sided component bounds with
`alpha=0.05/(2 readers * 2 arms)`; requiring both form tests is an intersection-union
decision, not a simultaneously covered two-form confidence region. The authored-world
exchangeability assumptions may fail. Exact single-proportion tail inversion follows
the [NIST binomial interval construction](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

[PLANNED-PRECISION.json](PLANNED-PRECISION.json) gives the actual denominators for
every offered policy/guarantee contrast and its conditional zero-error bound.
[PLANNED-COMPOSITION.json](PLANNED-COMPOSITION.json) distinguishes the two weightings.
No menu-impossible contrast is counted as an observed success. `analysis.py` preserves
unknown partial decisions and separates missing cells from wrong answers.

The prospective supplementary report uses 20,000 world-within-form/domain and
frame-family resamples, seed 2026091463, plus leave-one-frame-out sensitivity.
Whole-world resampling keeps that world's reader outcomes together. A zero-width
bootstrap interval at an empirical ceiling is expressly **not** an NI certificate.

## Reader identities and prerequisites

The existing local Gemma and Mistral model digests and their 14 September qualification
receipts are retained in [reader-config-review.json](reader-config-review.json).
Qualification validity ends on 21 September at 11:28:03 and 11:30:10 UTC respectively;
every launch must recheck dates, identities and settings. No qualification was rerun.

`prepare_live.py` performs only two local `GET /api/tags` requests and retrieval of
the immutable item artifact. It uses the actual SDK preparation path, verifies the
qualified settings digests, and creates a digest-bound planned manifest. It neither
loads model weights nor invokes an inference endpoint. `unbound-design-preview.json`
is only a local shape preview and must never be used as a launch commitment.

The bulky bank must be referenced by immutable URL and canonical SHA-256: an inline
manifest exceeds the SDK's 20 KB attempt limit. After the item commit exists, bind it:

```bash
python choose-any-final-package-2026-09-15/prepare_live.py --items-url IMMUTABLE_ITEMS_URL
```

The resulting bound planned manifest is suitable for a **non-writing preflight**,
not permission to mint or launch. The exact current preflight outcome and final pin
will be recorded in the follow-through note. A successful preflight is mint validity,
not scientific support, author approval, independent replication or ratification.

## Final author decision requested

Please inspect the actual items and serialized requests, not just this summary:

1. Confirm/correct the exact span rendering, the one shared deduplication clarification,
   semantic golds and held-out policy/guarantee task.
2. Confirm/correct the preserved assignment, actual reader/arm counts and separate
   official/equal-reader analyses. No reroll or outcome-dependent enlargement is offered.
3. Explicitly decide whether to lift the measurement pause for this **diagnostic** study
   after the live identity/preflight and independent-role conditions are actually met,
   or keep it held. Preparing the package is not inferred permission to launch it.

Bare-random remains deferred and unmeasured. This study tests present named readers
with complete careful English; it does not measure future tokenizers or future
training-data benefit. English's incumbent advantage is relevant context, not a
reason to discard current adverse evidence or assert future improvement.

See [PROGRESSION-HANDOFF.md](PROGRESSION-HANDOFF.md) for the independent replication,
governance and ballot path, including the remaining success-criterion mismatch.
