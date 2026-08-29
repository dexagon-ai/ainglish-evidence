# `each-group / groups-combined` comprehension carrier

Status: **answer-bearing inputs frozen; reader activation closed at 1/2 qualified lineages**.

The packet contains 192 scientific items, balanced 96 per form. Each of 96 scenario pairs uses the
same bare `across all ...` message and the same held-out question across two hidden intentions. The
marked and careful arms distinguish whether the claim applies to every named member separately or
to the all-records total only.

The answer labels and answer positions are exactly balanced 64/64/64. Three probes test a named
member's stated direction, whether that member may move oppositely without contradiction, and
whether the other aggregation level is asserted in the opposite direction. Questions use
`higher/lower/upward/downward` rather than repeating `increased/decreased` or either marker.

Every item carries a hidden two-group before/after table that is never shown to the reader.
`audit.py` independently recomputes the per-member and combined rates. The population includes
agreement worlds, one-member-opposes worlds, and both directions of Simpson reversal. This numeric
metadata tests item truth and supports later fidelity work; it must not leak into a comprehension
prompt.

Four immutable targets remain separate:

1. `each-group` versus bare ambiguous English;
2. `each-group` versus complete careful English;
3. `groups-combined` versus bare ambiguous English;
4. `groups-combined` versus complete careful English.

Forms and comparator classes must never be pooled. A bare comparison tests whether the ambiguity
was repaired; a careful comparison tests non-inferiority to explicit ordinary language. Neither is
independent governance evidence until a minted run uses at least two base-model lineages that pass
the same disjoint ordinary-English holdout.

No reader call, model download, attempt mint, second, measurement, or ballot is made by this
freeze. The installed-model audit currently leaves the roster at one qualifying Qwen lineage; all
other installed lineages have terminal retained failures, so activation would be invalid today.

Offline preparation and audit:

```bash
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python \
  group-aggregation-scope-comprehension-carrier-2026-08-29/capture.py
python3 group-aggregation-scope-comprehension-carrier-2026-08-29/build.py
python3 group-aggregation-scope-comprehension-carrier-2026-08-29/audit.py
```
