# Force-explicit `repeat-event / restore-state` token carrier v3

This zero-spend packet targets Excelsior's current force-explicit `-4` successor. It does not
relabel or reuse either superseded packet. Its 64 fresh affirmative pairs were authored for this
row: 32 per form, with four items from each form in each of eight predicate families.

`repeat-event` controls preserve an earlier matching event with the same resolved actor and
object. `restore-state` controls preserve only an earlier interval in which the explicit, entailed
result state held, plus the current asserted transition; they do not claim an earlier matching
event or same-actor cause.

Build and audit do not import tokenizers:

```bash
python3 repeat-restore-force-token-carrier-v3-2026-08-27/build.py
python3 repeat-restore-force-token-carrier-v3-2026-08-27/audit.py
```

Commit and push the exact generated packet before running `run_once.py`. The runner freshly checks
authenticated suggestions and the proposal, refuses unless the live row still requests an original
`token_delta`, mints an attempt before importing tiktoken, and files every finite direction. The
headline is the least favourable tokenizer value after equal weighting of the two forms. This is
price evidence only; it cannot establish comprehension or force projection.

