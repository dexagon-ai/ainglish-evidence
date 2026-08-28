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
