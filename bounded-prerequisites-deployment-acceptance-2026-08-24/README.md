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

At the recorded deployment, every runtime case passed but OpenAPI described the union on the wrong
role. The implementation is live; generated clients remain exposed until the narrow schema repair
is deployed. Repair PR: ai-nglish/ainglish-symfony #263 (private repository; only authorised
collaborators can inspect it).
