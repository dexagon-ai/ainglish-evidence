# Decide what a study can answer before running it

15 September 2026. Offline calculations only; no new inference or governance rule.
Reproduce with `python feasibility.py`. Full denominators and assumptions are in
[FEASIBILITY.json](FEASIBILITY.json).

## New findings

1. **The new choose-any form assignment does not also balance reader exposure.**
   The published mapping remains byte-for-byte pinned to
   `d4c1c6aa85abd335bd04ce996a0c4f1e78e14b92aaa6036568b2eb71a29c6c00`.
   For choose-any, Gemma receives 36 marked/36 English cells, but Mistral receives
   28/44. For draw-uniform the counts are 34/38 and 36/36. Holding each reader's
   accuracy identical across arms, unequal reader composition alone can produce
   an arm-pooled difference as large as **11.25 pp** for choose-any or **2.78 pp**
   for draw-uniform. These are algebraic stress bounds, NOT model results.
   Preserve the fixed assignment and official statistic; prospectively report
   the equal-reader average of within-reader differences as a separate sensitivity.
   Do not reroll to improve balance or silently swap the official estimand.

2. **The 144-world diagnostic is not a convincing five-point preservation study.**
   A conservative fixed-panel binomial reference, even with every answer correct,
   has lower marked-minus-English bounds of **−12.97 pp** and **−11.78 pp** for
   the two forms under the actual new marked-arm denominators. This is not an
   observed loss or a proof that every possible valid interval must be that wide.
   It shows why a diagnostic budget and a preservation certificate are different.
   Frame dependence can further reduce information. Author approval of a diagnostic
   does not approve enlarging it after seeing results.

3. **Verified-state's settlement tolerance is finer than a single answer in five
   of six strata.** Four strata have 24 cells per arm: one changed answer moves
   their contrast by 4.17 pp, against tolerances of 2.50–3.33 pp. The ledger-refuted
   stratum has 23/25 cells and 4.35/4.00 pp steps against 3.334 pp tolerance.
   The sixth has 29/19 cells; its steps are smaller than its 5.417 pp tolerance.
   The actual original and replication have overlapping aggregate intervals and
   similarly large negative pooled effects, yet all six strata fail the current
   reproduction rule. This helps explain why another well-executed run need not
   settle the record. It neither invalidates either study nor authorizes ignoring
   the rule. Inspect resolution before scheduling a third run; preserve the
   adverse evidence and use legitimate independent decision routes meanwhile.

4. **Zero errors in a small slice do not certify a five-percent ceiling.**
   Under independent binomial trials, zero errors in 8, 16, 32 and 40 observations
   give one-sided 95% upper error bounds of 31.23%, 17.07%, 8.94% and 7.22%.
   At least 59 zero-error independent observations are needed for this particular
   bound to fall below 5%, before multiplicity or clustering adjustments.
   Eight-case semantic review is valuable instrument preparation, not eight
   comprehension trials. A repeated question about one world is not a new world.

## Programme decisions

| Programme | Useful next deliverable | What it cannot presently certify |
| --- | --- | --- |
| none-of | Independent current-version assessment of the three already filed studies | New independent settlement from our own extra rows; future training benefits from prompt loading |
| may-not | Author admission/counting decision, blind clause screen, then paired-context instrument | 160 contextual rows as 160 independent clauses; five-percent false-inference bounds from tiny slices |
| impact/cause | Author assertion-gold and bare-fixed decisions, then a scoped original | World-state negatives from an unasserted axis; a routing score as pure lexical recognition |
| sanction | Finish bounded independent semantic review and pin one corrected candidate | Bare-word improvement or formal-act comprehension from the archive component alone |
| choose-any | Keep approved 144-world diagnostic scope; finalize exact comparator and analysis | Five-point NI proof, measured bare-random coverage, or a matching replica from a different model population |
| verified-state / verdict-fail | Current-version assessment, concrete instrument objections, actual eligible ballot receipts | Settlement from sign agreement alone; a comment as a vote; repeated rescue panels as progress |

There are three separate contrasts: cold marked versus ambiguous English; cold
marked versus full careful English; and entry-loaded versus cold marked language.
Report each honestly. English's training and tokenizer head start is relevant
context, not permission to erase current losses or count future gains as observed.

## Before any next original or replica

Name the question and current source/claim; freeze the full comparator, all golds,
sample units, primary and subgroup analyses; inspect realistic precision and source
settlement tolerances; establish an actually available independent role and exact
reader population; qualify, preflight and mint before target exposure. File adverse,
null and aborted outcomes. A diagnostic can still be worth doing, but label it as
such and do not promise it will ratify the proposal.
