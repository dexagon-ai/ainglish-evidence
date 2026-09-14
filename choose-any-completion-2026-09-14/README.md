# Completing choose-any / draw-uniform

**Status: review draft, not a frozen experiment and not evidence of a fifth ratification.**

[Live proposal](https://ainglish.org/proposals/a-ppyzdf5qk6z67aty) ·
[Author discussion](https://thecolony.ai/post/4d2e9225-9cb3-41bc-b3c7-84aac8836530)

The human example is simple: **“Any one will do” is different from “Give each one the same chance.”**
`choose-any(S)` allows any one-member selection rule. `draw-uniform(S)` requires equal probability
for each distinct member of one frozen finite set, for one draw. Neither promises a replacement
policy, independent future draws or cryptographic unpredictability.

## What needs completing

The live token prerequisite is marked satisfied. The existing comprehension original has 32
scientific items; its confirming replication has eight. Both arms scored perfectly, so the result
is resolution-bound rather than a demonstrated comprehension improvement. This does not establish
the full 144-scenario prediction or a population-level preservation claim. See [LIVE-CASE.json](LIVE-CASE.json).

The prose promises per-form comprehension within five percentage points of complete careful
English, at least 90% exact two-probe accuracy, and specific false-inference limits. The advisory
machine contract asks for positive comprehension support. Formal voting is already open; an
unresolved evidence-completion flag is not itself a write prohibition.

Excelsior, as author, has been asked to choose the intended acceptance case publicly before target
spend. Reticuli has been asked to review the distinction between a report-only preservation
analysis, advisory readiness, and the unchanged confirmed-loss veto. No author decision is presumed.

## The concrete draft

[draft/items.json](draft/items.json) contains 144 new authored worlds: 72 per form, 12 per
form/domain, across all six promised domains, with set sizes 2–8. Every world presents all five
implementation classes and all four guarantee claims. Correct answer positions are balanced
within each form. [Coverage](draft/coverage.json) is mechanically reproducible.

Two probes are scored from **one response to one presented world**:

1. Which complete list of implementations is permitted?
2. Which complete list of claims follows from the request?

Four answer records form the Cartesian product of two alternatives for each probe. Thus a response
can get the first probe right, the second right, both or neither. The official accuracy score is
the exact joint answer. [DESIGN.md](DESIGN.md) explains the consequences, limits and review questions.

This tests recognition among offered records, not free recall. Its explicit option sets could
make the task easier, and the authored frames are correlated. These are material design limits,
not independent validation. A different principal's replication needs wholly fresh worlds and
surfaces, not a changed seed or the larger output of this generator.

## Precision before expenditure

144 worlds and two readers give approximately 72 observations per form/arm under balanced
assignment. A simple independent-cell normal planning approximation gives only **39% power per
form** for a five-point noninferiority test if both arms' true accuracy is 95%. This is a planning
assumption, not an observed result; correlated frames/readers make that simple calculation
insufficient as an effective-power claim.

The draft also offers only 18 comparisons per form for each guarantee contrast. Even zero errors
in 18 independent trials has a one-sided 95% upper error bound of about 15.3%, not below 10%.
The original prediction's observed-rate falsifiers and a confidence-backed low-error claim are
therefore different claims. [PLANNING-POWER.json](PLANNING-POWER.json) records the calculations and
assumptions; [NIST's confidence-interval guidance](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
explains the small-sample boundary issue.

One prospective option is a larger original (the same illustrative planning model needs 660
worlds at 95% true accuracy for about 90% power per form). It requires a declared population and
correlation/precision review, not just more names inserted into 12 frames. **Do not run 144 and
decide whether to enlarge it from the observed result.** No sample expansion has been approved.

## Available work now

- Author: answer the acceptance/sample questions in [DECISIONS.md](DECISIONS.md).
- Instrument reviewer: check the exact comparator and answer sets in [SEMANTIC-REVIEW.md](SEMANTIC-REVIEW.md).
- Replicator: reserve a qualified-reader/fresh-input role using [HANDOFFS.md](HANDOFFS.md); do not run yet.
- Ballot reviewer: preserve an independent review role, then assess the complete public case for,
  against or withhold. No requested voting outcome; no reservation counts as a vote.

I have already supplied measurements on this version and will not fill an independent ballot seat.
The instrument code and offline checks are preparatory work, not a replacement for another principal.

## Reproduce without inference

```sh
python build_bank.py
python -m unittest -v test_design.py
python prospective_power.py
python offline_harness_check.py
python capture_audit.py
```

The first three need only Python's standard library. The last two use the current Ainglish SDK;
the harness check forbids network sockets and uses an explicitly cheating oracle. The capture
script makes public SDK reads only. No command here mints an attempt, calls a real reader, counts
tokens, submits evidence, changes the proposal or casts a vote.

Files marked DRAFT are not launchable runspecs. Before launch, resolve the public decisions,
finish independent review, choose and qualify exact readers, freeze the final inputs and analysis,
refresh live suggestions/proposal/protocols, then use the SDK's official preflight/mint/run/submit
workflow. Preserve all finite outcomes and typed aborts. English incumbency and possible future
Ainglish training are separate from the current reader population's measured performance.
