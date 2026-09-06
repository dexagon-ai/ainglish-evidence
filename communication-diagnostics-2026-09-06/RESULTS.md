# Communication diagnostic results

This is a constrained, reference-assisted interface test, not unrestricted communication or governance evidence.

| Phase | Arm | Fields | Correct | Parsed | Truncated | Mean input + output tokens |
|---|---|---:|---:|---:|---:|---:|
| reference | ainglish | 1 | 0/6 | 0/6 | 0 | 382.67 |
| reference | english | 1 | 0/6 | 0/6 | 0 | 406.50 |
| reference | ainglish | 2 | 12/12 | 12/12 | 0 | 392.67 |
| reference | english | 2 | 9/12 | 12/12 | 0 | 420.17 |
| reference | ainglish | 5 | 44/96 | 96/96 | 0 | 482.14 |
| sender | ainglish | 5 | 1/96 | 2/96 | 0 | 568.42 |
| handoff | ainglish | 5 | 26/96 | 96/96 | 0 | 482.48 |
| reference | english | 5 | 58/96 | 96/96 | 0 | 517.44 |
| sender | english | 5 | 25/96 | 43/96 | 0 | 626.11 |
| handoff | english | 5 | 47/96 | 96/96 | 0 | 518.86 |

Prospective communication-training gate passed: **False**.
Three authored contexts are reported separately in RESULTS.json. No original failed experiment was rerun or replaced.
