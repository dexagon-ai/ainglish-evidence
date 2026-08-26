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
