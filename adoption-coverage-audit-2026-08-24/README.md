# Post-ratification adoption-coverage audit

Evaluated `2026-08-24T22:15:30+00:00` against register `0.35.0`.

The audit refuses to turn absence of an instrument into an observed zero. A ratified
surface can be called sustained or not-yet-adopted only when a current scan was recorded
after ratification and its corpus window reaches that surface.

Snapshot digest: `c2a856f5839a91a10d85a722086b590c5e94a1751e61a0996e31713427fa1abe`.

## Result

- rows: 35
- coverage states: `{"current_post_ratification": 19, "not_applicable": 16}`
- unsafe served adoption claims: 0

## Reproduce

```bash
python build_audit.py
```

Until the first-class coverage receipt is deployed, the script derives the same rule from
legacy `computed_at`, `window_end`, `ratified_at`, and scanner-cadence fields and labels
that provenance explicitly. Re-run after deployment to verify every row switches to the
server-owned receipt without changing the scientific classification.
