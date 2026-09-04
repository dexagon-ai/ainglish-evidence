# `choose-any / draw-uniform` token replication v2

This is a fresh-input replication of Spark's `token_delta = -1.25` original, manifest `b69c504b…`. Sixteen complete operational messages are balanced across the two forms and compared with their complete careful-English meanings under the source roster: `cl100k_base`, `o200k_base`, and `p50k_base`.

The source is a legacy aggregate-only contract. The design declaration is retained in the canonical runner's plan but, correctly, is not added to the replication manifest when the target does not declare one. No settlement strata are invented.

Current tokenizers favour familiar ordinary English. This measures present token cost, not comprehension or future cost after Ainglish enters training data and tokenizer vocabularies.

## Filed result

The preregistered run completed with no gate or tokenizer failure. The least-favourable result was **−3.125 tokens**, with member means `cl100k_base = −5.9375`, `o200k_base = −5.875`, and `p50k_base = −3.125`. The row has `input_disjointness = 1.0` and is settlement-eligible.

The source value was −1.25. Under the governing legacy point-relative tolerance, the 1.875-token magnitude difference is an eligible disagreement (`reproduced_ok = false`), even though both results have the same favourable direction and both satisfy the proposal's declared `token_delta <= 0` prerequisite. This distinction is why settlement arithmetic must not be mistaken for the substantive evidence reading.
