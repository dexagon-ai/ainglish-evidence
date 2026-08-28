# `force-suspended` token recertification

Fresh-input recertification of the ratified construct's existing `token_delta` result.

The carrier freezes 32 new complete pairs before tokenization. Every pair keeps the registered
comparison used by the confirmed original: a constant careful-English mention-without-issuing
preamble versus `force-suspended` followed by the same remainder bytes. The population covers
assertions, requests, questions, promises, and permissions. The assertion stratum contributes
eight pairs and each other stratum six, so the overall pair count remains a power of two.

`run_once.py` starts with authenticated suggestions and a fresh proposal/target read, rejects any
complete-pair or arm overlap with every prior public `test_set` on the proposal, requires a clean
public source commit, and mints before importing or loading tiktoken. It then files every finite
direction once. The measurement prices only this fixed written comparison; it makes no claim about
comprehension, speech-act safety, adoption, or whether ordinary quotation is preferable.

Run the no-spend checks after publishing this source commit:

```bash
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python \
  force-suspended-token-recertification-2026-08-28/run_once.py --preflight
```

Omit `--preflight` exactly once to mint, tokenize, and file.

## Transport correction

The first attempt (`88689bfe-29c5-408e-a0da-6ce72229c7ca`) minted before tokenization and
computed the frozen result, but the server rejected submission because the tokenizer roster names
used an invalid `@vocab` suffix. The attempt was immediately aborted with its server receipt. The
retained cells are frozen in `transport-source.json`.

`transport_retry.py` is a transport-only successor. It changes the roster identities to the
server-required bare encoding names, discloses the failed attempt and retained result in its
manifest, and submits those exact cells without running either tokenizer again. It must likewise
be committed and pushed before execution.

## Result

The successor completed as attempt `43f55c26-828a-4e81-9398-1b3fbb66601c`; measurement
`20cb43ee7a3bed415228f919bb7adf34449acb1d1b59e4b26a09868b3babef8d` records:

- headline `token_delta = -4`;
- `tiktoken/cl100k_base = -5` and `tiktoken/o200k_base = -4`;
- `input_disjointness = 1.0`, `reproduced_ok = true`, and `settlement_eligible = true`;
- zero overlap across complete pairs, English arms, and Ainglish arms against all prior visible
  `test_set` rows on the proposal;
- `tokenizers_rerun = false` in the public successor receipt.

The result reproduces the confirmed original's point estimate for this fixed comparator. It does
not establish comprehension, safety under embedded speech acts, adoption, or a general advantage
over ordinary quotation. The server reports the roster as changed and has no shared per-member
identity with the legacy original; agreement is therefore point-level and member diagnostics are
report-only.
