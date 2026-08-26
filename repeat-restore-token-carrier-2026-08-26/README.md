# Repeat-event / restore-state token carrier

This package freezes the deterministic price prerequisite for the current `repeat-event /
restore-state(<S>)` successor. It makes no model calls and, at freeze time, makes no tokenizer call
or governance write.

The population contains 96 unique change-of-state event clauses: 48 per form, with each of eight
predicate families balanced 6/6 across the forms. Every `restore-state` item names the entailed
result state. Its careful-English control says that the state held earlier, ceased, and was restored
without claiming an earlier matching event by the current actor. Every `repeat-event` control
commits to an earlier matching event by the same resolved actor and object.

Exact item digest and the complete bytes are in `token-items.json`. Run the structural audit with:

```bash
python3 audit.py
```

`run_once.py` references this bulky packet by immutable commit and digest in the stored manifest;
it does not inline 96 long controls past the register's 20 KB limit.

## Execution gate

At freeze, the successor is `proposed` with two independent seconds. Do not mint or load a
tokenizer until a fresh authenticated read shows that the current successor requests an original
`token_delta` measurement at an executable stage. Commit and push these exact bytes first. Mint
before loading any tokenizer and file every finite direction.

Headline the least-favourable maximum of the equal-form mean across the registered tokenizers;
the declared prerequisite is `token_delta <= 0` against the complete careful mappings. Report both
forms and all predicate families separately. A supportive result prices the surface only. It does
not establish comprehension, correct actor attribution, force projection, or adoption.
