# Flagship adversarial-semantics gauntlet v2

Status: **protocol preparation; no inference results yet**

This development-only battery probes the semantic boundaries of all 18 pinned flagship examples.
It goes beyond pole recognition: it includes asymmetric cross-form relations, non-entailment,
quoted opposite-pole distractors, and two-record scope isolation. Every prompt supplies the exact
reference, so this tests reference-grounded application rather than cold comprehension.

The 180 frozen judgements use three labels:

- `entailed`: the candidate must follow;
- `contradicted`: the candidate must be false; and
- `underdetermined`: neither it nor its negation must follow.

Each construct contributes ten balanced items: two direct entailments, two curated cross-form
relations, two boundary overreads, two quoted-distractor items, and two dual-record scope items.
The asymmetric relations are intentional. For example, exactly one entails at least one, while a
permission does not itself establish possibility and a possibility does not grant permission.

The run uses three already-installed local models and performs no downloads. A model receives one
batch per construct. Missing, duplicate, malformed, or extra answer rows invalidate the entire batch
without retry. Both Ollama's `content` and `thinking` fields are retained, but only `content` is the
declared answer channel.

This is a copy, harness, and semantics diagnostic. It is not human validation, independent evidence,
or an Ainglish measurement eligible for governance.

```bash
python3 build.py
python3 audit.py
python3 run_ollama.py verify
python3 run_ollama.py run
python3 analyse.py results/responses.jsonl
```
