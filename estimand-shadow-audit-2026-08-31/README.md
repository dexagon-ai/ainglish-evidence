# Estimand shadow audit

Read-only audit of the live Ainglish dispute queue. It asks a deliberately
narrow question before the project adds another schema: how often can the
register recover the comparison contract it already tells replicators to
preserve?

For each disputed original and its settlement-bearing replications the capture
records whether the canonical manifest is retained, whether the attempt was
actually preregistered, and whether contrast, population/frame, aggregation,
instrument, and input-realisation declarations are recoverable. The heuristic
only reports visible declarations; it never decides that two studies are
scientifically comparable.

This is a shadow audit. It changes no evidence state, settlement relation,
legacy row, gate, or reward.

## Snapshot result

The 2026-08-31 capture covered 62 disputed originals and 158
settlement-bearing replications (220 rows total):

| Visible declaration | Rows |
|---|---:|
| Instrument | 220 |
| Free-text estimand | 140 |
| Canonical manifest available | 127 |
| Input realisation | 103 |
| Structured contrast | 50 |
| Structured population or frame | 35 |
| Structured aggregation | 27 |

Of 158 original/replication relations, 106 were underdetermined because one or
both canonical manifests were unavailable, 10 exposed a declared difference,
and 42 exposed no declared difference. The last category is deliberately not
called “comparable”: an absent or free-text declaration can conceal a real
difference.

The useful next step is therefore a small authoring aid that makes the
estimand dimensions inspectable in new manifests. These observations do not
justify changing settlement or rejecting historical measurements.

```sh
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python capture.py
```
