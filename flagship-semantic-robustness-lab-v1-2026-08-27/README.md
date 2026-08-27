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
