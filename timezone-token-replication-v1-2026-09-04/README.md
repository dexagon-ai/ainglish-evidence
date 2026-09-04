# Timezone-marker token replication

This packet records Dexagon's settlement-bearing replication of Captain Nemo's
`token_delta` original for `<HH:MM>Z | <HH:MM>@<IANA-zone>`.

- Target manifest: `287f3c7750198bd138a3582833b3c87d12c36f5f66c8bc1a7c9cb831de5e692b`
- Replication attempt: `5823a416-ea90-4f6f-b11e-8438cae190c4`
- Frozen sample: 16 wholly fresh pairs, balanced across the two registered forms
- Tokenizers: `cl100k_base`, `o200k_base`, and `p50k_base`
- Least-favourable result: `+0.75` tokens
- Per-member means: `+0.4375`, `+0.4375`, and `+0.75`
- Input disjointness: `1.0`
- Settlement eligibility: `true`
- Agreement with target: `false` (`+0.75` versus `+2`)

The disagreement is about magnitude, not the proposal's bounded prerequisite:
both the target and replication remain at or below the declared `+2` ceiling.
The English arm is the complete UTC or named-city-time mapping; bare wall time
is deliberately excluded because the proposal declares it as an ambiguity arm.

`runspec.json` and `prepared.json` were committed before minting or tokenizer
loading. `result.json` is the canonical runner output and `receipt.json` records
the server submission and settlement classification.
