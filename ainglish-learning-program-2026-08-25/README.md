# Ainglish learning-curve and fluent-adapter programme

This programme builds a rights-pinned corpus from the current, non-superseded ratified register and
trains a QLoRA adapter as a product/research demonstration. It is deliberately outside Ainglish
governance evidence: one trained model is not an independent principal, training on register text
contaminates cold-comprehension measurement, and a favourable adapter benchmark cannot ratify a
construct.

The development split withholds four complete semantic families. That adapter is evaluated for
format/generalization on seen constructs and transfer on the unseen families. Only after those
results are frozen may a separate release adapter train on all 19 ratified surfaces.

Base model: `Qwen/Qwen2.5-7B-Instruct` (Apache-2.0). Dataset contribution terms and source digests
are captured in `register-snapshot.json` and `manifest.json`.

`evaluate.py` records exact predictions, token-overlap F1, and exact registered-form retrieval.
These are deliberately modest reproducible diagnostics, not claims of general language fluency.
