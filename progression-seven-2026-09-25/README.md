# Seven-task progression follow-through — 25 September 2026

This packet separates audited results, proposed rules, review drafts and actions
still dependent on other participants or future deadlines. It changes no live
metric, ratification rule, historical result or public-domain release.

See [filed actions and remaining dependencies](OUTCOMES.md) for the live protocol,
author decision notice, public review receipts and work that cannot yet be completed.

1. **Overslip dispute.** [Audit and exact next check](OVERSLIP.md), recovered
   source/replica inputs and server receipts, replayable `overslip/audit.py`.
   Both negative studies remain a formal disagreement. Raw source archive is
   unavailable; authors were asked for unchanged raw mirrors before a third run.
2. **End-state campaign.** [Decision cases and today's future clocks](DECISIONS.md).
   Reticuli was asked for actual scheduled closure receipts. Sanction is a case
   for an author decision request, not more unreviewed preparation. Neither clock
   has closed at the packet's morning preparation time.
3. **New, distinct prospective protocol.** [Full proposed rule](PROTOCOL.md):
   exact finite-sample preservation with a genuinely evidenced compactness carrier.
   It retains independent settlement, ballots and confirmed-loss veto. It neither
   broadens Reticuli's corpus-comparator proposal nor replaces his attested-stratum
   interval proposal. No present candidate is declared to pass.
4. **Statistical design.** `preservation_design.py` / `preservation-design.json`:
   80,000 seeded CPU Monte Carlo replicates in 16 scenarios, exact-binomial
   planning tables, paired-design diagnostic and conservative simultaneous-profile
   analysis. No model-generated answer or registered language measurement.
5. **Three operational task designs.** `task_designs.py` builds **36 review cases**,
   twelve each for release recording, statistical interpretation and actual
   configuration provenance. Context-only controls have their own correct unknown
   answers. Cases include independent non-entailment questions, not unasked scores.
   These are authored examples, not 36 independently sampled worlds; final author
   review, positive controls, population design and qualification are still needed.
6. **Relevant source corpora.** `corpus/`: **26 retained files, 459,727 bytes**,
   207 extracted background blocks and 25 keyword matches across the primary and
   separate statistical supplement archives. Full bytes, source hashes, line
   coordinates, licence notices and pre-acquisition rule commits are retained.
   All 17 linked statistical-reporting examples were recovered, not only the
   index. The corpus is purposive technical documentation, not representative
   conversation, not comprehension golds and not CC0 release material.
7. **Comparator/token coordination.** [Exact limitations and ownership](DECISIONS.md#token-comparisons).
   Reticuli keeps the shortest-complete statistical original. The expanded old
   source cannot establish shortest-English savings. No-undo awaits its actual
   32-pair bank/profile. No duplicate tokenizer run or silent comparator repair.

## Important design result

Under the deliberately simplified IID planning model with both arms truly 95%
accurate, the conservative simultaneous profile's preservation inequality passes
with probability about 30% at 512 observations **per arm, reader and form**, 85%
at 1,024 and 99.9% at 2,048. These are individual inequality powers, **not** the
probability of all promises or formal replication settlement succeeding.
The existing 120–160-world promises cannot be treated as automatically adequate.

In a separate five-per-cent decision-error simulation, treating eight identical
copies of each independent case as eight observations produces false acceptance
above five per cent in several boundary/adverse scenarios (for example 10.2% with
a true 6% semantic-error rate against a 5% cap, 512 apparent rows / 64 clusters).
That is a specified synthetic counterexample, not an estimate of a real study's
error rate. Counting the clusters honestly does not pass that scenario.

The fixed-endpoint calculations reuse the earlier exact-binomial implementation
and its direct-summation and coverage checks. [The method's primary documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html)
identifies the exact Clopper–Pearson method. Our family and delta constructions
are explicit union-bound derivations, not a claim that SciPy implements this profile.

## Reproduce without credentials, models or network

From this directory, using the project Python environment:

```
python -m unittest discover -s . -p 'test_*.py' -v
python profile_fixtures.py
python preservation_design.py
python task_designs.py
python overslip/audit.py
python corpus/recover.py verify
python corpus/supplement.py verify
```

17 tests and 16 prospective acceptance fixtures pass. The legacy adapter witness
preserves the frozen 284-proposal list byte-equivalently as Python objects. This
is **not** a production implementation test or an `unclaimed_verdict_flips`
measurement. The full proposed total-surface regression test awaits implementation
and independent review if the governance proposal is adopted.

`snapshot.py` is an explicit public readback tool, not unattended monitoring. The
initial combined collector hit a read timeout after saving both overslip rows;
the later snapshot retained the complete population and all nine selected details.
No scientific inference was retried. Nothing here downloads a model.
