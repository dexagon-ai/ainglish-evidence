# Flagship token prerequisites

This packet prices two current, human-readable flagship candidates against the exact careful-English
controls declared by their proposals:

- `among-others / and-no-others`: 32 complete pairs, 16 per form;
- `this-once / from-now-on`: 16 complete pairs, eight per form.

Both packets are deterministic, balanced by form, power-of-two sized, and frozen publicly before
attempt minting. The headline value is the least-favourable maximum mean across `cl100k_base`,
`o200k_base`, and `p50k_base`; per-form and per-tokenizer values remain visible diagnostics.

These measurements price notation only. They do not establish comprehension.

Offline rebuild:

```bash
python3 flagship-token-prerequisites-2026-08-26/build.py
```

Live preflight or single-shot execution:

```bash
python3 flagship-token-prerequisites-2026-08-26/run_all_once.py --campaign among --preflight-only
python3 flagship-token-prerequisites-2026-08-26/run_all_once.py --campaign scope --preflight-only
python3 flagship-token-prerequisites-2026-08-26/run_all_once.py --campaign among
python3 flagship-token-prerequisites-2026-08-26/run_all_once.py --campaign scope
```
