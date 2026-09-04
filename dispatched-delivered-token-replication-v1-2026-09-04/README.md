# `dispatched / delivered` token replication v1

This carrier tests the release candidate's bounded token-cost prerequisite on 16 fresh complete
messages, balanced across `dispatched` and `delivered`, under the original tokenizer roster. Every
English comparator states the complete relevant meaning, including whether arrival is or is not
known and who witnessed it.

That choice is intentional. The original `token_delta = +2` row uses much terser English glosses
and does not declare a comparison identity. A replication that copied those phrasings would test
little beyond their wording. This run preserves the metric and tokenizer population while testing
whether the result survives semantically complete comparators. It may agree or disagree; either
finite result is filed once.

Current tokenizers have ordinary-English training and vocabulary advantages. This run measures
their present token counts. It does not measure comprehension, adoption, or the cost of a future
model or tokenizer trained on Ainglish.

## Filed result

The preregistered run completed without a gate or tokenizer failure. The least-favourable result
was **−4.125 tokens**, with member means `cl100k_base = −6.75`, `o200k_base = −6.625`, and
`p50k_base = −4.125`. The row has complete-pair `input_disjointness = 1.0` and is
settlement-eligible.

The source value was +2. Under the legacy point-relative rule this is an eligible disagreement,
not a confirmation. Both results remain inside the proposal's declared ceiling of +6, but their
opposite directions show that the token estimate is highly comparator-sensitive. The prerequisite
therefore remains unresolved pending another fresh settlement run. This token result does not
settle the separately adverse comprehension claim carrier.
