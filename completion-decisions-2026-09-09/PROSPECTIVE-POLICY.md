# Separate reproducibility of a quantity from satisfaction of a bound

Status: prospective discussion and retained-data shadow analysis. **No current
vote, confirmation, refusal or acceptance criterion is changed.** This document
extends the success-criteria discussion with a concrete cost example and safeguards.

## Decision A: what must a bounded cost prerequisite establish?

The replacement audit found three independent samples with headlines −0.75,
−0.125 and −0.5 tokens. Every tokenizer mean in every sample is within the declared
zero-cost allowance, but both replications correctly fail the existing ±0.075
point-agreement test. They disagree about *how much*, not the sample's sign.

Keeping exact quantity reproduction as the only route is simple and conservative,
but can make a threshold question depend on tiny reference-string changes. An
alternative is a separately named, **prospectively declared bound-verification
route**. It would verify that the cost of a defined message population remains
within its allowance, without falsely calling differing point estimates equal.

Advantages: the study answers the actual prerequisite; fresh samples can add
information instead of becoming pressure to tune until one number repeats.
Disadvantages: credible population uncertainty, a real sampling frame and explicit
decision rules are harder than comparing points. A permissive shortcut would
reward padded English, narrow easy populations and unreported adverse studies.

Minimum design before such a route could be adopted:

1. Declare full-information comparator, tokenizer population, allowance and actual
   independent sampling units before exposure. Reference aliases, repeated force
   prefixes and template copies are not extra independent messages.
2. Require a defensible one-sided upper uncertainty bound for the **worst named
   tokenizer's population mean**, with the tokenizer multiplicity and dependence
   dealt with explicitly. `member_span` measures spread across tokenizer means;
   it is not this uncertainty bound.
3. Preserve independent confirmation, source-quality checks, all attempted samples
   and audit-visible stops. An independent participant may verify the bound without
   claiming to have reproduced an unequal point estimate.
4. Define behaviour for mixed/bound-crossing studies before collection. Do not let
   the newest favourable study erase an older contrary one. Narrowing the population
   requires an explicit new claim and new evidence, not favourable subset selection.

**Recommendation:** prototype this as a shadow-only protocol specification first.
Do not expand the current tolerance or flip the replacement row's agreement flags.
The three existing member spans do not suffice to declare the alternative passed.

## Decision B: improved comprehension or preserved comprehension plus a benefit?

These are distinct hypotheses. For a preservation-plus-benefit route, independently
agree a meaningful noninferiority margin, adequate absolute/per-form accuracy,
the matched careful-English comparator, the current exposure condition and an
independently measured benefit. A non-significant difference from zero proves
neither preservation nor equivalence. A weak form cannot hide behind a mean.

The existing confirmed-comprehension-loss veto is a separate formal rule. A loss
inside an author's prose margin still invokes it today. Any decision to keep or
prospectively modify that veto must be explicit, independently ratified and covered
by adversarial fixtures; an advisory UI field cannot override it.

Preservation would admit useful compression that does not improve already-clear
English. Conversely, it adds degrees of freedom and can admit small real losses.
Keeping superiority is a legitimate stricter alternative, but then authors must
be told that preservation-only claims need revision or retirement.

## Historical shadow: deliberately no verdict flips

Run `python shadow_policy.py` after `analyze_followups.py`. Retained public cost
observations are compared with the zero bound; their message-population confidence
bounds are unknown. Completed reader diagnostics are shown against illustrative
−3-point and 90% checks to demonstrate why numeric screening alone is insufficient.
These numbers are not a newly chosen production rule and do not supersede the
proposal's full existing criteria. The script checks invalid comparators, changed
scope, non-independence, post-exposure collection, missing uncertainty and a bound
crossing. Every observed case remains **not qualified** under this incomplete shadow.

In particular, the calculation-supplied binary outcome study's high aggregate
accuracy cannot be substituted for the raw-calculation task, its weaker form,
independent confirmation, or the original joint-question criteria. Its full result
must remain beside the adverse and inconclusive diagnostics.

## English incumbency and future learning

Current models and tokenizers have had extensive English exposure. These studies
test the named current instruments, not future trained Ainglish. Supplying a
definition or a calculated fact is an exposure/task diagnostic, not evidence that
model weights or tokenizer vocabularies have changed. Future training can be a
separate prospectively evaluated benefit, never an automatic discount on current
harm. A current penalty also does not prove a distinction permanently unsuitable.

## Next independent decision

Review the two routes separately: first agree the scientific claim and safeguards;
then freeze a normative protocol and adversarial examples; only then implement
server/SDK/UI parity and collect qualifying prospective evidence. Publish the
non-migration rule explicitly. No code in this evidence repository changes the
register or stages a language release.
