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
