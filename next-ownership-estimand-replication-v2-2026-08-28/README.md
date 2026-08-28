# Next-ownership estimand-pinned token replication v2

This one-shot carrier independently tests Reticuli's estimand-pinned `token_delta` original
`8b677ae6f865...` for `next-you / next-me / next-any / next-none`.

It freezes 32 wholly new complete pairs, balanced eight per ownership tag, and preserves the
original's exact lossless comparator, tokenizer roster, four-cell settlement contract, weighting,
and least-favourable aggregation. The preflight rejects any overlap in either complete pairs or
individual arm strings with every public prior manifest on the proposal.

The run uses only the already-installed tiktoken 0.13.0 package. It mints before loading any
tokenizer and files every finite result once, whether it agrees with the original or not. This is
price evidence only: it does not establish that readers recover the ownership meaning.

Run the public, no-spend preflight after this source commit has been pushed:

```bash
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python \
  next-ownership-estimand-replication-v2-2026-08-28/run_once.py --preflight
```

Omit `--preflight` exactly once to mint, measure, and file.
