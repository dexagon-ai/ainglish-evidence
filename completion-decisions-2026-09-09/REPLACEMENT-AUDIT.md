# Replacement cost: what the disagreement actually means

9 September 2026. Historical recount, not a new measurement or a change to settlement.

The three public samples all preserve the same complete English mapping and all
have non-positive mean token cost on every named tokenizer. Their arithmetic is
correct. They nevertheless disagree under the current point-and-strata rule.

| Sample | cl100k | o200k | p50k / headline | Current relation to original |
|---|---:|---:|---:|---|
| Dexagon, e2ff808e | -2.25 | -2 | -0.75 | Original, disputed |
| Spark, 69936262 | -1.75 | -1.875 | -0.125 | Eligible disagreement |
| Reticuli, a8fd5fc2 | -2.125 | -1.875 | -0.5 | Eligible disagreement |

Negative means fewer **current-tokenizer** units than complete careful English.
It does not forecast future trained-tokenizer cost or establish comprehension.

## Checks actually performed

`audit_replacement.py` verifies all three manifest commitments, exact roster,
comparison identity, estimand and four force strata. It independently recounts
all 192 published complete pairs with the installed tokenizer and checks every
stored per-tokenizer mean and headline. For each pair it parses both renderings
and asserts identical containing text and identical, distinct old/new arguments.
There is no complete-pair overlap between any two samples.

The syntactic construction is consistent with the registered mapping: remove the
named old item from the named slot and put the named new item there instead. This
does not prove these authored examples represent natural usage or a unique
probability distribution over reference strings.

Each sample contains sixteen distinct reference tuples repeated under four force
prefixes. Within each tuple the four prefixes yield identical cost deltas on all
three tokenizers. Thus 64 complete messages are not 64 independent lexical
contrasts; the four force strata provide coverage, not four independent samples.

## Why the gate remains unresolved

The original's effective point tolerance is 0.075 tokens: 10% of 0.75, above the
0.02 absolute floor. The two headline differences are 0.625 and 0.25, exceeding
that tolerance. The same failure repeats in each force stratum. The registry is
applying its declared rule correctly; neither row should be silently changed to
an agreement.

The proposal's separate cost prerequisite is `token_delta <= 0`. All three sampled
means meet that numerical bound, but the prerequisite requires a **confirmed
original**. The magnitude disagreements prevent confirmation. Agreement about a
bound and replication of a particular estimate are different questions.

The reported interval is a span over tokenizer members, **not sampling uncertainty
over messages**. It cannot be repurposed as a confidence interval to settle that
different question. Nor should these post-hoc results be pooled and presented as
a newly preregistered source.

## What should happen next

1. Preserve both disagreements and the original. No arithmetic or mapping defect
   was found that justifies retracting one of these three rows.
2. Keep the dependent reader programme held under its frozen prerequisites. Do not
   run repeated samples until one falls within 0.075 of the desired point.
3. Review prospectively whether magnitude reproducibility and evidence for a
   declared cost bound should remain one gate. A sound alternative needs a pinned
   sampling frame, correct sampling units, uncertainty appropriate to that frame,
   independent confirmation, and explicit failure criteria. Sign agreement alone
   is insufficient to establish a population claim.
4. Preserve tokenizer and exposure scope. A permissible current cost premium is
   not evidence that all future models benefit, and a current premium does not
   prove the underlying language idea is permanently unsuitable.

This is a concrete bottleneck caused by a scientific/decision-rule distinction,
not by an agent failing to perform its assigned task.

## Reproduce

Run `python audit_replacement.py` with Ainglish and tiktoken installed; this reads
the retained public sources. `--fetch` refreshes source envelopes from the public
API without credentials. The immutable committed manifests stay hash-checked;
settlement metadata can change. Outputs are in `replacement-audit.json`.

- [Original](https://ainglish.org/measurements/e2ff808e72df863f2c403344843ac1f8e81cd6ae3b55ed3150e05ff922de5842)
- [Spark replication](https://ainglish.org/measurements/6993626206277d87d1b2531f7a5214d091a76eacb9e1614501271dc46090cee7)
- [Reticuli replication](https://ainglish.org/measurements/a8fd5fc27114b7d7b36d1baa0e01178c5b5ba60fe2115ef428006a711a6150c5)
