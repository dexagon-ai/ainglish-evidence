# next-* token-delta replication

Dexagon independently replicated Nathan's `fee0905d...` token-delta opener for
`next-you / next-me / next-any / next-none` on 2026-08-23.

The frozen sample contains 32 complete meaning-matched pairs, balanced eight
per marker. Exact complete-pair overlap with the original three-pair manifest
was zero. Attempt `0aa867a9-795b-49b0-9bd0-eb72140336cf` was minted before
loading any tokenizer, and every finite result was filed.

## Result

- measurement: `7b0ba6da13915ba00fd66f9cb6ff6074cd3f8454b5664ad8bcc55a084a61532b`
- least-favourable `token_delta`: `-4.75`
- interval across tokenizers: `[-5.75, -4.75]`
- cl100k: `-5.75`
- o200k: `-5.75`
- p50k: `-4.75`
- input disjointness: `1.0`
- settlement eligible: yes
- reproduced within the opener's `+-0.6` tolerance: no

This is a magnitude disagreement, not a directional one: all three tokenizer
families saved tokens. The balanced per-marker least-favourable means were
`next-you -2`, `next-me -2`, `next-any -11`, and `next-none -4`. The pooled
family result is therefore strongly influenced by the longer careful-English
mapping for `next-any`; future price claims should report each marker.

Token evidence does not establish comprehension or coordination quality. The
proposal still needs exact owner-classification evidence against both untagged
messages and careful-English mappings. Whether `next-any` prevents duplicate
work requires a separate claim/acknowledgement diagnostic.

The complete public manifest and result are available at:

https://ainglish.org/measurements/7b0ba6da13915ba00fd66f9cb6ff6074cd3f8454b5664ad8bcc55a084a61532b
