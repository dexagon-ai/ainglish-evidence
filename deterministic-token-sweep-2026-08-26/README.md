# Deterministic token sweep — 2026-08-26

This package freezes three original token-prerequisite campaigns for current human-readable
Ainglish candidates:

- `they-one / they-many` — 32 pairs, 16 per form;
- `next-up / next-week` — 32 pairs, 16 per form;
- `different-from / different-across` — 32 pairs, 16 per form.

Every pair compares the registered marker with the proposal's complete careful-English meaning,
not with the ambiguous short phrase it replaces. Pair populations are unique, balanced by form,
power-of-two sized, and public before attempt minting. Three tiktoken 0.13.0 encodings are priced;
the headline is the least-favourable maximum tokenizer mean. No comprehension claim follows.

`rather-not / fine-either-way / would-welcome` and `extra-retries / total-attempts` were deliberately
excluded: their filings pin exact 36- and 24-pair estimands, conflicting with the current
power-of-two token protocol. Changing those counts would change the estimand rather than execute it.

```bash
python3 deterministic-token-sweep-2026-08-26/build.py
python3 deterministic-token-sweep-2026-08-26/run_all_once.py --campaign they --preflight-only
python3 deterministic-token-sweep-2026-08-26/run_all_once.py --campaign they
```

