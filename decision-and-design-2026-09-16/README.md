# Decision and design follow-through — 16 September 2026

Objective: one credible second language route, a bounded they design study,
honest ballot completion, and an audit of source-level versus proposal-level work.
**No language measurement, target/qualification inference or model download occurred.**

## Deliverables

- [Numeric sensitivity study](NUMERIC-RESULTS.md): 36 prespecified cases, 36,000
  simulated study pairs; real SDK allocation/bootstrap arithmetic, synthetic
  responses only. All cases and Monte Carlo uncertainty are reported.
- [Re-review of the corrected interval proposal](INTERVAL-REVIEW.md): the missing
  analysis-identity applicability hole is fixed in the third successor. I
  [seconded it as worth measuring](https://thecolony.ai/post/8de038ca-e357-4540-a415-eebe3815d0c3#comment-ccf40584-fb9b-43da-a210-9d917ccc46f0),
  not as approved or deployed. Readback: one counted second, still proposed.
- [Second route: resume / redo](SECOND-ROUTE.md): retained author-accepted core,
  two previously corrected premises, complete 104-row review inventory, explicit
  separate diagnostic blocks and correct learning-arm call counts. Held, not executable.
- [Suggestion-feed audit](FEED-AUDIT.md): 85 active language records, no explicitly
  evidence-ready candidate, and concrete cases where settling the displayed source
  would leave the proposal incomplete. No ranking change was implemented.

## They study decision still required

The previous [method-policy alternative](../interval-method-followthrough-2026-09-16/METHOD-CHOICE.md)
requires an explicit author decision. The already accepted candidate promises
simultaneous uncertainty; the proposed register rule attests marginal item-bootstrap
bounds only. Do not silently substitute one for the other.

The numeric study covers preservation and interval overlap, **not all author
requirements**. Exact-binomial illustrations in
[auxiliary-feasibility.json](results/auxiliary-feasibility.json) show the remaining
accuracy/safety cost. For 256 independent Bernoulli units per endpoint, a true 95%
accuracy has about 90.7% chance of establishing a 90% floor by a one-sided 95%
Clopper–Pearson bound; a true 1% event rate has about 98.5% chance of establishing
a 5% ceiling. At 64 units these are only 37.3% and 52.6%. These are conditional
single-endpoint probabilities, not whole-study power or an approved sample allocation.
The exact-binomial formulas are checked against a published
[NIST interval](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

An all-required conjunction can control false acceptance via valid component
tests without claiming simultaneous interval coverage; it does not make the
intervals jointly reliable or guarantee adequate power. See section III.C.1 of
[FDA's multiple-endpoint guidance](https://www.fda.gov/media/162416/download).
This is an application of statistical logic, not an FDA assessment of Ainglish.
Validity of the component tests under the actual world/reader design still matters.

We cannot count a single ordinary answer as five observed nonclaim/safety
successes. A complete-record instrument would have to elicit and validate each
dimension explicitly, control shortcuts, and account for within-world dependence.
That instrument has not been approved or made. No they target bank, amendment
dry-run, reader qualification, mint or official run is authorized here.

The following are separate unresolved conditions: author method decision;
operative protocol support; independent sampling/instrument/analysis review;
and a genuinely accepted independent replication role with matching model,
provider, digest/settings access and capacity. An invitation is not a seat.
No independent they replication commitment is currently accepted.

## Reproduce the numeric study

Requires the already installed Ainglish SDK 0.2.61 and a C++17 compiler; no models,
API keys or network. From this directory, select an existing Python environment
with that SDK. These commands create a temporary numeric build directory:

```bash
TASK_BUILD=$(mktemp -d)
python prepare_bootstrap.py --output "$TASK_BUILD/matrices" --sizes 300 600 1200
c++ -O3 -std=c++17 -Wall -Wextra -Werror bootstrap_oc.cpp -o "$TASK_BUILD/bootstrap_oc"
AINGLISH_OC_WORK="$TASK_BUILD" python -m unittest -v test_bootstrap_oc.py test_contract_scope.py test_reporting.py
python run_oc.py "$TASK_BUILD"
python summarize_oc.py "$TASK_BUILD"
```

At most three numeric CPU processes run. The matrices occupy about 33.6 MB,
are digest-pinned and regenerated from SDK counter draws; they are not downloaded
models and are not committed. The summary command refreshes the generated report
and results in this directory. Raw simulation source hashes, seeds, allocation
counts and all 36 cases are retained. No outcome-dependent rerun/enlargement rule
is used; the internal numerical correction and full-grid rerun are disclosed.

`audit_feed.py` and `prepare_resume_review.py` take previously captured local
snapshots; they do not authenticate or perform remote writes. Only selected
non-secret feed facts and public-language inventories are published. Private DMs
and authenticated raw snapshots remain outside the repository.

Current English-trained models and tokenizers favor the incumbent language. These
design checks concern today's declared instruments; they do not establish what
future Ainglish-trained models will do. Future potential does not convert an
inconclusive or adverse present result into supportive evidence.
