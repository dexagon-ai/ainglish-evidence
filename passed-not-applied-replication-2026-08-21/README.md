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

## Filed outcome

- Frozen source: `edc877a`
- Attempt: `cc3e47df-1f47-4bd0-a978-9e85ece94bc1` (completed)
- Measurement: `16ebaf1e4f80ccf9bd3ff6a43c342a9b7639b7ba717bb19537112acff7b7421c`
- Least-favourable value: `+0.125` tokens
- Tokenizer-mean range: `[-1.875, +0.125]`
- Server result: `input_disjointness=1`, `panel_neff=3`,
  `settlement_eligible=true`, `reproduced_ok=false`

The cl100k and o200k lineages each measured `+0.125`; Gemma measured `-1.875`.
Thus the fresh sample does not reproduce the original `-1.5` point value, and
the apparent saving is tokenizer-dependent. The complete cells and immutable
server response are in `receipt.json`.

The first local invocation stopped before minting or loading any tokenizer:
the SDK's local validator rejected an overlong model identity. The identity was
shortened without changing the pinned tokenizer, then source was recommitted
and republished as `edc877a` before the successful mint.
