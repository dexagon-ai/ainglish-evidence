# Bounded-prerequisite deployment acceptance

This is a public, non-mutating acceptance matrix for the bounded evidence-prerequisite protocol.
It clones the served `some-or-all / some-but-not-all` proposal into an unfiled draft and exercises
the authoritative `/api/v1/preflight` endpoint. It does not consume a proposal allowance or write
register state.

Run with an installed Ainglish SDK:

```sh
python3 run_acceptance.py --output receipt.json
```

The runtime matrix checks legacy strings, both valid bound directions, malformed bounds, boolean
bounds, unknown keys, duplicates across roles, and the prohibition on bounded claim carriers. It
also checks whether the served OpenAPI schema places the object union on prerequisites rather than
claim carriers.

The first recorded deployment passed every runtime case but described the OpenAPI union on the
wrong role. Repair PR ai-nglish/ainglish-symfony #263 subsequently corrected that public schema.
The 2026-08-28 rerun passes both the full runtime matrix and the repaired OpenAPI role contract.
