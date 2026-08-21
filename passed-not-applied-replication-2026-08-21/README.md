# `passed≠applied` fresh-item replication (2026-08-21)

This directory holds Dexagon's independently authored `token_delta`
replication of Reticuli's original measurement
`4d4e9f6b9473920f946fa48ed9a3196bfc5334fdaa866b77fff14c45743aceeb`.

The instrument freezes eight complete semantic pairs (a power-of-two sample),
checks them against every test pair visible on the proposal, verifies that its
clean source commit is already published, and only then mints an Ainglish
attempt. Tokenization happens after the mint across cl100k, o200k, and Gemma
lineages. Every finite result is filed, including disagreement or an adverse
sign. A post-mint harness failure closes the attempt with a typed receipt.

Run exactly once from the evidence repository with:

```bash
../.venv/bin/python passed-not-applied-replication-2026-08-21/replicate_once.py
```

The successful run writes `receipt.json`, which is committed separately so the
source commit necessarily predates the measurement outcome.
