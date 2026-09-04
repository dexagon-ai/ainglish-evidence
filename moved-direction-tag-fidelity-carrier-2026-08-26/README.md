# `moved-earlier / moved-later` tag-fidelity carrier

No-spend freeze for the missing `tag_fidelity` prerequisite on the current measured successor.

The packet contains 96 controlled-use cases: 32 genuinely earlier changes, 32 genuinely later
changes, and 32 cases where neither registered direction is warranted because the schedule is
unchanged or the comparison baseline is missing or contradictory. Events span meetings,
maintenance, jobs, ballots, deadlines, deliveries, audits, and releases. Answer positions are
exactly balanced.

`audit.py` independently parses every timestamp-bearing source event and re-derives whether the
replacement is earlier, later, unchanged, missing its baseline, or contradictory. It refuses if
the derived warranted tag differs from the frozen answer. This ground-truth check leaves the
published item bytes and digest unchanged.

The estimand is the least-favourable exact warranted-tag fraction across separately qualified
reader lineages. This controlled-use diagnostic is not organic adoption evidence and does not
establish cold comprehension. The packet is frozen before any attempt or model call and must not
run until at least two reader lineages pass an independent ordinary-English holdout.

Offline reproduction:

```bash
python3 moved-direction-tag-fidelity-carrier-2026-08-26/fetch_live_snapshot.py
python3 moved-direction-tag-fidelity-carrier-2026-08-26/build.py
python3 moved-direction-tag-fidelity-carrier-2026-08-26/audit.py
```

`build_local_qualification.py` adapts the two target-independent qualification
receipts filed on 2026-09-04 into the legacy runner's immutable roster format.
After that two-lineage receipt exists, `run_once.py --qualification <repo-relative-selected-result>`
is the only execution path. It verifies that immutable receipt and all local digests, requires a
clean public commit, refreshes personalized suggestions and the current proposal, verifies that
the executing principal is not the proposer, and mints before the first
reader call. It retains exact, inexact, null, adverse, and transport outcomes without retry and
files the least-favourable lineage score. The qualification path is explicit rather than a mutable
"latest" pointer.

## Filed result

Attempt `79efbec4-36fc-4daf-8af6-4da17e268731` filed a least-favourable
`tag_fidelity` of **0.9479167** across the two qualified reader lineages.
Mistral scored 0.9791667 and Gemma scored 0.9479167. Mistral's earlier/later/
neither scores were 0.9375/1.0/1.0; Gemma's were 1.0/1.0/0.84375. All 192
cells were retained without retry. This completes the missing original
controlled-use fidelity diagnostic; it does not settle the separately routed
comprehension replication or establish organic adoption.
