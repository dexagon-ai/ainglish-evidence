# Flagship semantic robustness lab v1

This development-only battery covers all 17 pinned flagship candidates under four controlled
surface conditions: canonical Ainglish, hyphen loss, careful English, and an opposite-pole
distractor before the actual message. Each condition contains both semantic poles.

The test supplies the exact two-pole reference in every prompt. It therefore diagnoses whether
already-installed models can follow and preserve a flagship distinction under controlled surface
changes; it does **not** measure cold comprehension, human intuition, organic adoption, or
proposal evidence. Its three-model roster is a convenience sample, not a representative panel.

The plan makes 51 calls: one batch per construct for each of three model families. Temperature is
zero, the seed and context are fixed, malformed or missing cells count as incorrect, and no retry
or post-result prompt tuning is allowed. No additional model may be downloaded for this run.

Before execution:

```bash
python3 flagship-semantic-robustness-lab-v1-2026-08-27/build.py
python3 flagship-semantic-robustness-lab-v1-2026-08-27/audit.py
```

`run.py` additionally refuses unless these bytes are committed and public at `origin/main`.

## Result

All 51 frozen calls completed once, with no retry and no download.

| Model | Parseable calls | Mechanical cells | Interpretation |
|---|---:|---:|---|
| Qwen 3.5 9B | 0/17 | 0/136 | output-channel/harness failure; not a semantic score |
| Gemma 3 12B | 17/17 | 134/136 | 98.53% |
| Mistral Small 3.2 24B | 17/17 | 136/136 | 100% |

Qwen reported 261–263 generated tokens and a normal stop on each call, but returned an empty
`response` field every time. The frozen runner did not retain a separate thinking field. Its
mechanical zero therefore cannot be interpreted as choosing the wrong semantic pole; it exposes a
harness/output-channel defect. The run is not retried or repaired.

Across the two interpretable families, canonical, careful-English, and hyphen-loss cells were all
68/68. Opposite-distractor cells were 66/68. Both misses were Gemma on
`true-as-worded / false-as-worded`: it followed the contrast sentence instead of the explicitly
labelled actual message. Mistral classified those cells correctly.

These prompts supplied each exact two-pole definition. The high scores show that two installed
models can apply the distinctions under this controlled reference-grounded task; they do not show
cold comprehension, human intuition, training-data adoption, or evidence eligible for ratification.
`analysis.json` retains the exact interpretation and follow-up boundary.
