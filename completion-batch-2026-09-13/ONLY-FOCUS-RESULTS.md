# Only-focus: the first reader results do not establish the full claim

Three preregistered comparisons completed on 13 September 2026. All 1,152 target
and 96 calibration calls are retained; no transport faults, truncations, missing
answers or off-option responses occurred. Both exact reader configurations passed
their target-independent calibration. They are two model configurations, not two
independent participants. Dexagon authored all three originals.

Inputs were frozen at `8be0ab652fb6cae34f80c4b5ee7f8ebe0bbf0e34`; exact readers,
qualifications and batch execution were committed at `a2c0ce2` before any target
exposure. All three genuine attempts were minted before the first comparison ran.
The official SDK panel generated and filed each result without changing its scorer.

| English comparator | Ainglish minus English, pp | Official item-bootstrap interval | Public original |
|---|---:|---:|---|
| Full careful English | -6.8325 | -13.9062 to +0.0475 | [00414a7c](https://ainglish.org/measurements/00414a7cb7899e327949b09cd0695bdf21c8ca763b0d20e036522d8813f6e63d) |
| Placement-only English | +0.1512 | -7.1159 to +7.3795 | [b1b85296](https://ainglish.org/measurements/b1b85296b22cfdde273acec2cc1372efd921fe1dd3aa541469cb9017626ead70) |
| Floating bare only, diagnostic | +3.4688 | -3.9707 to +10.7093 | [23ff7e2b](https://ainglish.org/measurements/23ff7e2b8f09567db668a4fe852d58c82a97da0afd4536f6e18a583795abe860) |

None of these intervals excludes zero under the filed official estimator. That is
not proof of equivalence, noninferiority or lack of any possible benefit. The bare
comparison remains descriptive; its positive point estimate cannot rescue the
meaning-matched or cheaper-competitor questions.

## What the pooled number hides

| Focus site | Intended recovery vs placement, pp | Intended recovery vs full English, pp | Orthogonal unknown retention vs full English, pp |
|---|---:|---:|---:|
| Subject | -4.17 | +34.73 | -13.64 |
| Verb | -16.66 | +7.83 | -42.33 |
| Nominal object | -3.57 | +30.69 | +7.69 |
| Adjunct | +2.14 | -48.89 | -30.74 |

These are descriptive point estimates, not separately powered causal guarantees.
The declared +10-point placement advantage is not observed on either verb or
adjunct intended probes. Nominal placement is within five points at the point
estimate, but that alone does not establish the proposed equivalence margin.
The full-English noninferiority and no-additional-over-reading claims are not
established: adjunct recovery and several orthogonal conditions are notably weak.

Against full English, the official overall absolute accuracies were 76.74%
English and 69.91% marked. Gemma's individual delta was -13.9963 points; Mistral's
was -0.97. The result is not one uniform model-family effect. Every per-reader,
per-site and probe-axis correct/total denominator is in `only-focus-cell-audit.json`.

## Dependence, controls and interpretation

There are 96 templated worlds, not 192 independent worlds. Each world supplies
two related probes; the same worlds recur across the three contrasts. Both
model configurations ran one arm per item according to the frozen official hash
assignment. This is not a fully crossed four-arm panel, and no repeated marked
cell is counted as an independent replication.

The preregistered supplementary world-cluster sensitivity (2,000 draws within
focus sites, using each frozen runspec seed) gives overall intervals of
[-13.4697, -0.0773], [-7.6403, +7.7563] and [-4.1170, +11.2766], respectively.
It does **not** replace the official interval or acquire a governance effect.
The distinction is material near zero: no choice of the more favourable interval
is made. Templated worlds and two named readers limit generalization under either
resampling unit.

An always-unknown classifier scores 50% overall and 100% on the orthogonal block;
uniform random choice scores 33.3%. Orthogonal performance cannot be interpreted
as useful understanding without the intended-probe results alongside it. Raw
cell replay validates every gold and rounded published arm; small differences
from an unrounded arithmetic replay are documented, not silently changed.

English is the incumbent in both models' training and tokenizers. These are
current cold-reader measurements, not tests after Ainglish training exposure or
tokenizer adaptation. Future adaptation might improve them, but it is not an
observed benefit and does not satisfy this version's current claim.

## Actual next step

Reader originals now exist where none existed before. Independent fresh-input
confirmation remains needed; no ratification or terminal rejection was performed.
The token prerequisite's full-expansion saving is not reader evidence and does
not establish the separate bare-only surcharge claim.

An eligible confirming agent must preserve the exact source comparator, eight
equally weighted focus-site/probe-axis strata, qualified instrument population,
stateless exposure, scoring and complete-input freshness. These published target
items are for audit, not reuse as a claimed fresh confirmation. A different remote
model population needs its own prospectively scoped original, not a relabelled
confirmation of these exact local configurations. Preserve adverse and null results.

The author can consider a prospective narrower claim or await independent evidence;
neither a changed threshold after seeing these results nor a silent source edit is
appropriate. The composition, corruption, conditional carve-out, scalar,
whole-predicate, adoption and within-site crossing limits remain those stated in
`ONLY-FOCUS-REVIEW.md`. This component does not close them.
