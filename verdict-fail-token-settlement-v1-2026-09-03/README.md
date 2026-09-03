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
