# Evidence-contract coherence audit

`audit_live.py` reads all visible live proposal stages plus `/api/v1/protocols` and finds a narrow,
reproducible contradiction: a proposal explicitly accepts a positive metric value while its formal
prerequisite invokes generic protocol stance semantics that classify that same value as opposing.

The first rule covers `token_delta`, whose generic protocol is lower-better around neutral zero.
It quotes the exact matched sentence and number. Ambiguous prose about a positive cost against one
baseline and savings against another stays in `manual_review`; the script does not guess which
comparison a filed scalar uses.

Run with the project virtual environment:

```bash
/home/dexagon/codex/dexagon/.venv/bin/python audit_live.py --write
```

The generated snapshot is evidence of the live population at its timestamp, not a permanent claim
about rows that may later be amended or superseded.

Version 2 treats bounded prerequisite objects as first-class acceptance relations and emits an
exact per-row remediation. A contract amendment is substantive hypothesis metadata: the successor
re-enters at proposed and must earn new attention and evidence; predecessor rows remain visible but
must not be silently carried or reinterpreted.
