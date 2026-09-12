# Small panels can give misleadingly confident preservation claims

The [frozen plan](PRESERVATION-PLAN.md) at evidence commit `8dec5ca` was published
before execution. All 4,800 simulated experiments are summarised in
[the result artifact](preservation-simulation.json), with Monte Carlo intervals,
source digest and software version. No model inference, language measurement,
official policy change or historical reinterpretation occurred.

At a true loss of exactly 2 percentage points, a hypothetical test must not
routinely declare the loss smaller than its 2-point margin. In this simulation:

| Explicit simulated setting | Naive cell bootstrap false preservation | Item-only | Reader × item |
|---|---:|---:|---:|
| Crossed effects, 2 readers × 128 items | 30.5% | 30.75% | 26.5% |
| Crossed effects, 8 readers × 128 items | 29.25% | 29.75% | 5.0% |
| Near ceiling, 2 readers × 16 items | 53.75% | 53.75% | 53.75% |

These percentages are observations over 400 experiments per row, not exact
population rates or recommended panel sizes. The paired generator, dependence
assumptions and probabilities are fully specified in the code. Equality cases
are retained too: the crossed method's power at true equality was only 25.25%
with two readers and 19.25% with eight in these settings. More conservative
uncertainty can reduce false claims while also making real preservation harder
to establish; this is not a universally best-method contest.

The near-ceiling failure has a simple cross-check. Under that generator each
paired cell differs with probability .02. The probability that all 32 paired
differences are zero is `.98**32`, approximately 52.39%. Every ordinary empirical
bootstrap then returns a zero lower bound, despite the population being exactly
at the prohibited loss boundary. More bootstrap draws cannot reveal outcomes
absent from the observed sample.

## Consequence for the prospective protocol review

Do not replace a superiority gate with a mechanical “lower bound > -margin”
without demonstrating calibration of the actual estimator at the intended
reader/item sample sizes and dependence structure. A reader × item label is
necessary for some questions but not sufficient for valid small-sample bounds.
Finite-sample safeguards, clear unresolved states, and a prospectively justified
design are preferable to interpreting every zero-width ceiling as success.

This study deliberately used complete paired outcomes. It is not a test of the
current counterbalanced CAD implementation, a theorem about every bootstrap,
or permission to require eight independent reader lineages for all proposals.
The illustrative margin does not become a project default. Separate practical
benefit, absolute understanding, valid questions, per-form obligations and
independent confirmation still need their own evidence. The confirmed-loss
veto and Reticuli's no-retrospective-rescue commitment are unchanged.
