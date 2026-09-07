# Contextual teaching and structural transfer

These are synthetic current-model learning results, not proposal evidence.

- Seed 17, matched-training: +1.562pp; screen passed.
- Seed 17, careful-english-retention: -2.083pp; screen passed.
- Seed 17, ordinary-english-retention: +21.875pp; screen passed.
- Seed 29, matched-training: +2.083pp; screen passed.
- Seed 29, careful-english-retention: +2.083pp; screen passed.
- Seed 29, ordinary-english-retention: +17.708pp; screen passed.

All declared point screens passed: False.

## Limits

- One cached Qwen2.5-7B family, two training seeds, synthetic single-author tasks. Not independent human validation or governance evidence.
- 192 semantic configurations instantiate24 authored frames. More domains or rows are not192 independent task structures.
- Frames exercise reference tracking, temporal state, action traces, joint constraints and boundaries absent from the simple single-question teaching rows. Task-local background sometimes supplies relevant boundary rules in both arms; this is not wholly unassisted understanding. Related reasoning may occur in prior published tests; novelty is relative to this frozen training split, not globally unseen concepts.
- The model and fixed tokenizer already know English. This is modest adapter learning, not a future large-scale pretraining or tokenizer-replacement forecast.
- All four adapters must be trained and publicly digest-sealed before any heldout evaluation. No adaptive epochs, favourable seed selection, post-hoc re-scoring or uncertain-call retry.
- No full model checkpoints or downloads. Existing cached models remain untouched. Total new adapter allowance is2GiB with at least15GiB physical host reserve.
- 2000 paired bootstrap draws resampling24 authored structural frames, seed2026090770. Every output and failed qualification retained. Qualification is per model condition; unqualified conditions have no invented target score. Ordinary-English rehearsal/retention are related authored families, not an independent benchmark.
