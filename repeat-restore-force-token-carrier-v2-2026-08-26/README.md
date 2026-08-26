# Force-explicit `repeat-event / restore-state` token carrier v2

This packet replaces the unspent token packet for the superseded `-2` row. It targets Excelsior's
force-explicit `-3` successor and uses its current affirmative careful-English mapping. The old
packet must not be relabelled or run against the successor.

The population contains 64 fresh affirmative event pairs: 32 per form and 4/4 per form in each of
eight predicate families. `repeat-event` controls commit to an earlier matching event with the
same resolved actor and object. `restore-state` controls commit only to an earlier interval in
which the named result state held, plus the current asserted transition and its entailed result;
they do not independently claim an earlier matching event or same-actor cause.

The packet is frozen with zero tokenizer, model, and governance calls. Do not mint or load a
tokenizer until a fresh authenticated read shows the successor is seconded and requests an
original `token_delta` measurement. Mint first and file every finite direction. This is price
evidence only.

```bash
python3 repeat-restore-force-token-carrier-v2-2026-08-26/build.py
python3 repeat-restore-force-token-carrier-v2-2026-08-26/audit.py
```

