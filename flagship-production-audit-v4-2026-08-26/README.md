# Flagship production audit v4

This fail-closed audit targets the complete publication state after Symfony PRs 294, 295, and 296:

- exactly 17 live catalogue entries and no local overlay;
- complete problem, before, two-pole after, consequence, and claim-guard copy;
- every pinned proposal exists and is current;
- the force-explicit repeat/restore `-3` successor is pinned, never superseded `-2`;
- `/road-to-register` is live;
- every available catalogue entry has a live candidate-detail page and a machine receipt link.

`probe.py` is read-only and may report an incomplete deployment. `capture.py` writes `audit.json`
only when every gate passes, so a partial deploy cannot become a positive publication receipt.

```bash
python3 flagship-production-audit-v4-2026-08-26/probe.py
python3 flagship-production-audit-v4-2026-08-26/capture.py
```

