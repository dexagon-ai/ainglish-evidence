# Acknowledgement speech-act token prerequisite

This one-shot carrier freezes the token-price arm for
`ack-as-receipt(<R>) / ack-as-agreement(<R>)` before any tokenizer is loaded.

The manifest contains 168 paired semantic cells: 84 exact principal/reference situations,
each rendered once as receipt and once as agreement, balanced across six declared domains.
Every cell preserves four text arms for later use: the Ainglish form, bare `acknowledged`,
a short practical-English competitor, and the shortest careful-English expression used by
the proposal's declared token prerequisite. No reader or model has seen these cells.

The settlement value is the least-favourable tokenizer mean across the already-installed
`cl100k_base`, `o200k_base`, and `p50k_base` resources, with receipt and agreement weighted
equally. The proposal accepts a value no greater than `+2`. This is price evidence only:
even a strong saving cannot establish comprehension, avoid overreading agreement as a promise
to comply, or make the proposal ready to ratify.

Run the no-tokenizer preflight after the source commit is public:

```bash
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python \
  acknowledgement-speech-act-token-original-2026-08-28/run_once.py --preflight
```

Omit `--preflight` exactly once to mint, measure, and file every finite result.

