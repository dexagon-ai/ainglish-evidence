# Ratified-flagship adoption coverage

Captured `2026-08-27T08:27:34+00:00` from the live flagship catalogue.

This is a fail-closed coverage audit, not a new scan. It keeps observed zero distinct
from missing observation and does not refile redundant evidence while the server-owned
post-ratification receipts remain current.

## Result

- ratified flagships: 9
- safe current receipts: 9
- unsafe served adoption claims: 0
- adoption states: `{"not_yet_adopted": 1, "sustained": 8}`
- earliest receipt expiry: `2026-09-01T07:51:59+00:00`
- audit digest: `d3695cbf9ab91b8cff69cffbef96aa381581100ee945625809e100688208eccc`

## Decision

No manual observation is warranted now. Let the scheduled scanner refresh the readings;
fail the public adoption claim closed if any receipt reaches expiry first.

## Reproduce

```bash
PYTHONPATH=/path/to/ainglish/src python capture.py
```
