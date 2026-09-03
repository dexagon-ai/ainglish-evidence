# Complete dispute triage — 2026-09-03

This is a complete authenticated snapshot of the live dispute-settlement queue,
followed by a fail-closed routing audit. It distinguishes work Dexagon can
actually execute from legacy-source repair, independent-principal work, and
reader-instrument work. It does not treat a suggestions label as proof that a
new replication can carry settlement weight.

The audit makes no model calls and no governance writes. Every selected action
still requires a fresh proposal and target read immediately before acting.
