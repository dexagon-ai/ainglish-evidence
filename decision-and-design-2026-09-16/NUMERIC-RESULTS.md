# Numeric design sensitivity: all prespecified cases

**Not observed Ainglish evidence. No target or qualification inference occurred.**

Two forms, two synthetic readers, 1,000 independent simulated original/replica pairs
in every case. N is distinct synthetic worlds **per form**, so one run has 4N
target cells. Intervals use the SDK 0.2.61 hash allocation and 2,000 SHA-counter
bootstrap draws, with the proposed common-mask per-form reading. These are
marginal item-bootstrap intervals, not simultaneous confidence coverage.

“Both pass + overlap” requires pooled and both form lower bounds >= -5 pp,
no exactly-zero/exactly-one form arm in either study, and pooled/form interval
intersection across studies. This is **CAD preservation plus numeric overlap**,
not the complete commensurability/independence/settlement pipeline or ratification.
It excludes token benefit, qualifications, author accuracy/safety endpoints and ballots.

Parenthesized bounds are 95% Wilson **Monte Carlo** intervals for a simulated
frequency, not confidence intervals about the language. They are pointwise,
not simultaneous over this table. Method: [NIST](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

| Scenario | N | Cells/run | Original pass | Both pass + overlap (MC interval) | Original held: degenerate | Form-0 / form-1 / pooled coverage |
|---|---:|---:|---:|---:|---:|---|
| equality_independent | 300 | 1200 | 64.0% | 40.1% (37.1–43.2%) | 0.0% | 94.7% / 93.9% / 94.7% |
| equality_shared_world | 300 | 1200 | 57.8% | 35.9% (33.0–38.9%) | 0.0% | 93.4% / 94.4% / 95.3% |
| tolerated_two_point_loss | 300 | 1200 | 15.9% | 2.6% (1.8–3.8%) | 0.0% | 94.6% / 94.5% / 94.2% |
| five_point_boundary | 300 | 1200 | 0.2% | 0.0% (0.0–0.4%) | 0.0% | 94.9% / 94.3% / 94.9% |
| six_point_violation | 300 | 1200 | 0.0% | 0.0% (0.0–0.4%) | 0.0% | 95.7% / 95.0% / 94.3% |
| boundary_shared_world | 300 | 1200 | 0.1% | 0.0% (0.0–0.4%) | 0.0% | 94.0% / 94.8% / 95.1% |
| violation_shared_four_world_frame | 300 | 1200 | 0.1% | 0.0% (0.0–0.4%) | 0.0% | 86.7% / 85.5% / 85.7% |
| equality_shared_four_world_frame | 300 | 1200 | 64.7% | 42.3% (39.3–45.4%) | 0.2% | 94.1% / 95.7% / 95.2% |
| equality_near_ceiling | 300 | 1200 | 0.5% | 0.0% (0.0–0.4%) | 99.5% | 100.0% / 99.8% / 99.4% |
| opposite_reader_effects | 300 | 1200 | 62.6% | 39.7% (36.7–42.8%) | 0.0% | 95.9% / 94.0% / 94.7% |
| one_harmed_form_hidden_by_pool | 300 | 1200 | 0.1% | 0.0% (0.0–0.4%) | 0.0% | 93.3% / 95.5% / 94.8% |
| one_percent_absent_at_random | 300 | 1200 | 64.9% | 40.5% (37.5–43.6%) | 0.0% | 94.1% / 94.4% / 94.1% |
| equality_independent | 600 | 2400 | 94.9% | 89.6% (87.6–91.3%) | 0.0% | 95.0% / 95.2% / 96.2% |
| equality_shared_world | 600 | 2400 | 94.2% | 86.6% (84.3–88.6%) | 0.0% | 94.8% / 94.2% / 94.4% |
| tolerated_two_point_loss | 600 | 2400 | 43.9% | 20.5% (18.1–23.1%) | 0.0% | 95.9% / 95.4% / 95.5% |
| five_point_boundary | 600 | 2400 | 0.1% | 0.0% (0.0–0.4%) | 0.0% | 93.8% / 93.7% / 93.8% |
| six_point_violation | 600 | 2400 | 0.0% | 0.0% (0.0–0.4%) | 0.0% | 96.1% / 95.3% / 95.1% |
| boundary_shared_world | 600 | 2400 | 0.2% | 0.0% (0.0–0.4%) | 0.0% | 94.7% / 94.5% / 95.2% |
| violation_shared_four_world_frame | 600 | 2400 | 0.0% | 0.0% (0.0–0.4%) | 0.0% | 84.6% / 86.6% / 86.6% |
| equality_shared_four_world_frame | 600 | 2400 | 94.7% | 88.2% (86.1–90.1%) | 0.0% | 95.1% / 95.3% / 96.0% |
| equality_near_ceiling | 600 | 2400 | 4.1% | 0.3% (0.1–0.9%) | 95.9% | 99.6% / 99.7% / 98.5% |
| opposite_reader_effects | 600 | 2400 | 95.7% | 90.4% (88.4–92.1%) | 0.0% | 95.1% / 93.2% / 93.8% |
| one_harmed_form_hidden_by_pool | 600 | 2400 | 0.0% | 0.0% (0.0–0.4%) | 0.0% | 94.4% / 95.3% / 95.0% |
| one_percent_absent_at_random | 600 | 2400 | 95.6% | 89.9% (87.9–91.6%) | 0.0% | 95.1% / 95.0% / 94.2% |
| equality_independent | 1200 | 4800 | 100.0% | 98.9% (98.0–99.4%) | 0.0% | 94.1% / 94.8% / 95.7% |
| equality_shared_world | 1200 | 4800 | 100.0% | 98.7% (97.8–99.2%) | 0.0% | 95.3% / 93.8% / 94.5% |
| tolerated_two_point_loss | 1200 | 4800 | 84.2% | 70.2% (67.3–73.0%) | 0.0% | 94.4% / 95.1% / 94.8% |
| five_point_boundary | 1200 | 4800 | 0.1% | 0.0% (0.0–0.4%) | 0.0% | 95.0% / 94.1% / 94.8% |
| six_point_violation | 1200 | 4800 | 0.0% | 0.0% (0.0–0.4%) | 0.0% | 95.0% / 94.4% / 94.4% |
| boundary_shared_world | 1200 | 4800 | 0.2% | 0.0% (0.0–0.4%) | 0.0% | 95.5% / 94.6% / 94.5% |
| violation_shared_four_world_frame | 1200 | 4800 | 0.0% | 0.0% (0.0–0.4%) | 0.0% | 86.9% / 86.9% / 87.2% |
| equality_shared_four_world_frame | 1200 | 4800 | 99.8% | 98.1% (97.1–98.8%) | 0.0% | 93.8% / 95.4% / 96.3% |
| equality_near_ceiling | 1200 | 4800 | 21.1% | 5.5% (4.2–7.1%) | 78.9% | 97.7% / 98.0% / 95.6% |
| opposite_reader_effects | 1200 | 4800 | 100.0% | 98.7% (97.8–99.2%) | 0.0% | 93.8% / 93.7% / 94.4% |
| one_harmed_form_hidden_by_pool | 1200 | 4800 | 0.0% | 0.0% (0.0–0.4%) | 0.0% | 94.5% / 95.0% / 94.9% |
| one_percent_absent_at_random | 1200 | 4800 | 99.9% | 98.6% (97.7–99.2%) | 0.0% | 95.2% / 94.4% / 95.6% |

## Consequences for choosing a study

- At 95% accuracy in both arms, the numeric joint pass/overlap frequency rises
  from 40.1% at 1,200 target cells/run to 89.6% at 2,400 and 98.9% at 4,800.
  These are conditional synthetic operating characteristics, not a selected N.
- At marked 94% versus careful-English 96%, even the 4,800-cell envelope gives
  only 70.2% joint pass/overlap. In 626/1,000 study pairs that also pass/overlap,
  the original pooled interval excludes zero below. That is 626/702 of those
  numeric successes: a tolerated-loss test does not remove the separate current
  confirmed-loss veto. This study does not create a formal confirmation.
- At 99.9% equality, 78.9% of originals are held at 4,800 cells and only 5.5%
  of pairs pass. Refusing zero-variance certainty is defensible, but this method
  may be inefficient near ceiling. Do not degrade the comparator, seek a worse
  reader or rerun until errors occur to evade the guard.
- When four nominal worlds share an unmodelled frame, the violating case has
  only about 85–87% coverage. Nominal 95% labels do not repair pseudoreplication.
  Sample independent world units or predeclare an appropriate clustered method;
  paraphrases/option swaps are not extra independent worlds.
- Opposite reader effects can average away. This simulation uses the actual
  per-arm reader-cell allocation, not an assumed equal-reader estimand. It does
  not establish per-reader safety or generalize to unmeasured models.
- “One percent absent at random” is a sensitivity calculation, not a blanket
  permission to discard outputs. Empty/unparsed/fault outcomes must obey the
  official harness and its preregistered denominators and yield guards.

No final sample size, bank, author amendment, accepted replication seat or run
has been authorized by this report. Near-ceiling, dependent and safety cases
must be considered by the independent design reviewer, not filtered away.

## Reproduction and numerical correction

See README.md for the commands. Source hashes and the complete fixed scenario
list/streams are pinned by results/design.json. Matrix hashes and arm counts
are published; the 33.6 MB of regenerable binary matrices are not committed.
Seven native/SDK parity and boundary tests passed. Four separate rule-scope
witness tests are illustrative specification checks, not production tests.

An internal initial run accumulated expected cell probabilities in floating
point, producing spurious coverage failures for zero-width intervals around
a true zero effect. Before publication this was fixed using exact homogeneous
probabilities or analytic allocation-weighted reader means, with explicit
zero-truth and perfect-guard tests. The entire unchanged 36-case grid was rerun.
Decisions/overlap/coverage now use four-decimal half-away-from-zero published
bounds; raw quantiles are used for SDK parity checks. This is a simulation
correction, not an alteration of any measured language outcome.

The two simulated executions are statistically independent streams, not
independent human/agent participation. Actual independence requires real
separate participants and independently authored, disjoint inputs.
