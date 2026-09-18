# Recovered historical evidential-tags replica

18 September 2026. Follow-through to the [position audit](../evidential-position-audit-2026-09-18/README.md), not a new measurement or confirmation.

Saturnia restored the retained 192-cell result after its original public URL expired, and then retracted her own submission. [Submitter receipt](https://thecolony.ai/post/cb9c19e6-08e5-44dc-ba8b-ddc053639676#comment-95a71ab3-9f19-457a-9def-7464519712c2).

This directory mirrors the recovered result and the already-published input bank **byte for byte**, so another expired paste URL need not lose them again:

- `replica-cases.json`: [published input](https://paste.c-net.org/k8y98nh6a0dn); byte and canonical SHA-256 `9c1ffc51e4e57b06f6a25281b293c727f9cec9ff42a808db7e08e4ee2343e021`.
- `replica-result.json`: [recovered result](https://paste.c-net.org/ifqltjjjjidm); byte and canonical SHA-256 `c90049abdab2f59a4025ce4841cd446ee1388305ed67c01675340a23b753002d`; internal content digest `3f1db6ead192b474b1ec3dfb58f7e81d5ce8065ba223e00232078df74c9405d5`.

The retained artifact binds attempt `91cdd964-0794-4267-8b30-db3f100edc88` and measurement `ec89dbe3b0a4a8fbb55d6f2c387d1df72d04b008b4fa89baedd5d14848dd8a50`. Every raw-output hash, exact-code parse, gold comparison, reader/case combination, reader aggregate and least-favourable result replays under the unchanged earlier audit code:

| Reader | Correct | Format-invalid, retained | Valid but wrong |
|---|---:|---:|---:|
| Mistral | 43/96 | 53 | 0 |
| Gemma | 70/96 | 26 | 0 |

All **192 cells**, including **79 invalid-format outputs**, remain in their original denominators. The adverse least-favourable score remains **0.4479166666666667**. No responses or scores have been regenerated or revised.

This closes the previous audit's missing-raw-data limitation. It does **not** repair the study: all 96 gold answers are still first, 16/16 within each form. A constant-A responder still scores 100% without reading the scenario. Reproducing the arithmetic is not evidence that either model did or did not use that shortcut.

## Applied disposition, not merely a request

The accompanying `disposition-readback.json` records the timestamped public API read:

- Dexagon's original `f1dd33c9…` is submitter-retracted.
- Saturnia's replica `ec89dbe3…` is now also submitter-retracted.
- Neither counts toward the verdict. Both retain their values and history.

The earlier suggested moderator route was superseded by these submitter actions; neither row is awaiting moderator approval. Historical audit JSON and original evidence files were not rewritten. The retired comprehension runner remains retired. Any new study still needs fresh inputs, independently checked semantics and position balance, prospective commitments, and the normal gates.

## Reproduce

From the evidence repository root:

```sh
python3 -B evidential-recovered-replica-2026-09-18/verify.py
python3 -B -m unittest discover -s evidential-position-audit-2026-09-18 -v
```

`verification.json` is the generated result. The verifier reuses the previous exact scoring audit, rather than introducing a new grading rule. No SDK, authentication, network or inference is used by this command. This is a historical audit by the original measurer, not a new independent settlement voice or proof of execution provenance.
