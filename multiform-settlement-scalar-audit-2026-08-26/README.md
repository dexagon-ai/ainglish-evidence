# Multi-form replication settlement: scalar-only blocker

This audit explains why the frozen preference, persistence, and may comprehension replications
must not be launched yet even after a two-lineage reader roster exists.

Each target is a multi-form claim whose manifest says the forms are reported separately. The live
measurement write schema, however, accepts one top-level `value` and has no `per_form`, `strata`,
or cell-result field. The public replication contract says agreement is determined within the
relative/absolute tolerance of that value. Consequently, a replication can reproduce the pooled
scalar exactly while moving individual form estimates in opposite directions by 30 percentage
points. The live surface would receive no form estimates with which to reject that false agreement.

`capture.py` records only public API material: the OpenAPI measurement schema, the public protocol
settlement rule, and the three content-addressed target measurements. `audit.py` verifies the
snapshot digest, absence of a form-level settlement input, exact target identities and balanced
fresh-carrier form weights, then executes the three synthetic cancellation witnesses.

This is a fail-closed orchestration finding, not evidence about any Ainglish construct. The safe
next step is a protocol amendment that binds declared strata and requires every load-bearing form
to satisfy the replication rule; alternatively the original must be superseded by separately
filed per-form estimands. Until then, do not let pooled agreement settle these rows.

```bash
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python \
  multiform-settlement-scalar-audit-2026-08-26/capture.py
python3 multiform-settlement-scalar-audit-2026-08-26/audit.py
```
