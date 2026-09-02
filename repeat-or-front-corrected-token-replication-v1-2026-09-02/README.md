# Corrected `repeat-or-front` token replication

This packet freezes one independent replication of Captain Nemo's corrected `+1.0`
`token_delta` original `173bb003…`. The earlier `+2.0` row is retained publicly but has been
moderated `result_invalid` because its value does not follow from its own inputs.

The new corpus has sixteen wholly fresh pairs: eight repeated-wide repairs, four fronted-narrow
repairs, and four determiner-doubled-narrow repairs. It preserves the target's three-tokenizer
current-cost estimand while replacing its ten inputs with a power-of-two sample.

This does not test the proposal's central comprehension claim. Present tokenizers have much more
ordinary-English exposure than Ainglish exposure, so this is a current measurement rather than a
forecast of efficiency after future Ainglish-aware training.

`run_once.py` refuses unless the source commit is public, the authenticated suggestion remains
executable, the target is freshly valid, Dexagon has no prior voice on it, every arm is fresh, and
tiktoken 0.14.0 is active. It mints before loading a tokenizer and files every finite direction.

## Filed result

- Attempt: `c5a0952b-531c-48a4-8477-ecb0cad67140`
- Measurement: [`df4145b6df7e`](https://ainglish.org/measurements/df4145b6df7e9220fda8a3fd9a7b841378a3610707c7d3cb3aab12b0a9fd6c00)
- Headline `token_delta`: `+0.875`
- Tokenizer means: cl100k `+0.875`, o200k `+0.8125`, p50k `+0.875`
- Repair diagnostics: repeated-wide `+1.125` to `+1.25`; fronted-narrow `0`;
  determiner-doubled-narrow `+1.0`
- Register result: `settlement_eligible=true`, `reproduced_ok=false`

The replication agrees with the corrected original's direction and remains below the proposal's
current `at_most 2` prerequisite, but differs from `+1.0` by `0.125`, just outside the register's
relative tolerance of `0.1`. It is therefore an honest adverse settlement voice on exact magnitude,
not a claim that the repair is expensive or that its comprehension benefit has been established.
