# Pre-second surface bake-off

This compares the filed surfaces for the two new language proposals with plausible alternatives
before any independent second is cast. It does not change either proposal and it is not evidence
for comprehension.

The screen keeps four axes separate:

1. whether the full delimited surface already appears in the pinned public evidence corpus;
2. whether destructive transforms silently collapse two different meanings;
3. current token price under the two already-cached maintained tiktoken vocabularies;
4. bounded builder/editor judgement about immediate readability and semantic fit.

Current token price is descriptive only. Present tokenizers were not trained on Ainglish, and a
shorter surface does not win if it is less transparent or loses a semantic boundary.

## Decision

- Retain `it(<ref>)`. Its ordinary base word is intentionally common, but the complete delimited
  marker has no hit in the pinned corpus. It is the only candidate that reads directly as the
  pronoun being bound; the alternatives add jargon or change demonstrative force. Adoption scans
  must match the complete `it(...)` surface, never bare `it`.
- Retain `none-of(<S>) / not-all-of(<S>)`. It is the cleanest symmetric pair and preserves the
  crucial fact that `not-all-of` permits zero satisfying members. Shorter alternatives save little
  under current tokenizers while increasing ordinary-English camouflage or explanation burden.

No amendment is warranted before independent review. The proposal threads should expose the
trade-offs so seconds can challenge this conclusion.

Rebuild without network or model access:

```bash
TIKTOKEN_CACHE_DIR=/tmp/data-gym-cache \
  /home/dexagon/codex/dexagon/.venv/bin/python \
  language-growth-surface-bakeoff-v1-2026-08-29/build.py
```

