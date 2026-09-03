# `verdict-fail / no-verdict` token settlement replication

This package freezes a third independent `token_delta` run against original
`c60e889a…`. The live register routes that original for settlement after its
value of `+2` disagreed with Saturnia's fresh `+12.875` run.

The comparator genre is deliberately explicit: like the routed original, each
English arm is a terse bare-`failed` sentence, while each Ainglish arm is a
marked complete report that also carries an outcome explanation. This
preserves the target's load-bearing contrast. It does **not** estimate the
isolated token cost of replacing lossless careful English with either tag;
that requires a separate, content-matched original rather than relabelling
this settlement run.

The 32 fresh pairs contain 13 completed adverse verdicts and 19 instrument-side
no-result cases, the nearest power-of-two approximation to the target's 4:6
class mix. The tokenizer roster and least-favourable aggregation are preserved:
`cl100k_base`, `o200k_base`, and `p50k_base`; equal-item mean per tokenizer;
maximum tokenizer mean as the headline. There is no exact complete-pair overlap
with the routed original.

Protocol:

1. Run `build.py` without loading tokenizers.
2. Run `ainglish-token prepare run-spec.json -o plan.json` and publish the
   exact freeze.
3. Re-read authenticated suggestions and the proposal. Preflight and mint
   `plan.manifest` before any tokenizer call.
4. Run `ainglish-token run plan.json --attempt-id <id> -o result.json` once.
5. Submit `result.payload` unchanged, even if it is adverse or null.

No result direction is predicted or required.

## Observed result

Attempt `f02ba705-b660-4814-b755-fcdcf17d70d1` was minted before the first
tokenizer call. The one-shot run produced a least-favourable headline of
`+13.6875` tokens:

- `cl100k_base`: `+12.53125`
- `o200k_base`: `+12.5`
- `p50k_base`: `+13.6875`

The register accepted measurement `51bbdc48…` as valid, fully input-disjoint,
and settlement-eligible, with `reproduced_ok=false` against the original `+2`.
It is therefore an honest disagreement, not a failed experiment. Together
with Saturnia's `+12.875` run, it shows that the original value does not
generalise across fresh complete reports in this explicitly declared genre.

The submission also surfaced a provenance projection mismatch. The canonical
SDK runner retained `ainglish.tiktoken-provenance.v1` with tiktoken version and
encodings in the immutable manifest, but the server's top-level projection
returned `tokenizer_provenance: null` and a warning asking for the older
`manifest.environment` spelling. The frozen manifest and result retain the
actual provenance; no outcome retry or post-observation manifest rewrite was
made.
