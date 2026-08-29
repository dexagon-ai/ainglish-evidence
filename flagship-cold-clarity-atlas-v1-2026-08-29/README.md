# Flagship cold-clarity atlas v1

Status: **complete; see [`RESULT.md`](RESULT.md)**

This development-only atlas compares six live, editorially legible Ainglish candidates across five
conditions and six already-installed model families. It asks operational consequence questions;
surface recognition alone cannot score a cell.

The five conditions are:

1. canonical Ainglish with no definition (`ainglish_cold`);
2. the byte-identical canonical message after one exact live-register definition card
   (`ainglish_defined`);
3. complete, meaning-matched careful English (`careful_english`);
4. deliberately underspecified bare English (`bare_english`); and
5. a controlled spacing or punctuation corruption that is intended to preserve direction
   (`corrupted_ainglish`).

The bare arm is not assigned a hidden intended pole. Its correct answer is that the message leaves
the load-bearing distinction unspecified. This avoids pretending a reader can recover information
that the text does not contain. The one-card arm measures immediate accommodation, not prior
training-data inclusion. Current cold and token behavior may disadvantage Ainglish because current
models were trained on ordinary English; future-trained performance remains a hypothesis.

Each construct contributes eight balanced consequence frames per condition. Calls are batched only
within one construct and one condition, so no prompt exposes another arm. Answer positions are
deterministically shuffled per cell. Missing, malformed, duplicate, or extra answer rows invalidate
the entire eight-cell batch without retry.

This is project-designed, project-operated development research. It is not human validation,
independent evidence, a registered Ainglish measurement, or a ratification recommendation. Every
item in this packet is permanently development-only and must be excluded from later governance
evidence.

## Reproduction

Preparation and execution are deliberately separate:

```bash
python3 capture.py
python3 build.py
python3 audit.py
# Commit and push every preregistered byte before inference.
python3 run_ollama.py verify
python3 run_ollama.py run --workers 2
python3 analyse.py
```

The runner verifies exact local model digests and the public preregistration commit before the first
call. It has no download path and never invokes an Ollama pull endpoint.

## Frozen result

All 180 calls and 1,440 cells completed without a download or retry. The preregistered primary
classification is adverse: all six constructs remain `amendment_candidate` under the complete
denominator. Seventeen batches were invalid—seven Ollama HTTP failures and ten strict output-contract
failures—and remain in that denominator.

The retained valid-batch sensitivity is more discriminating. `they-one / they-many` reached 97.5%
cold and 100% after one card; role cardinality reached 100% after one card; claim-source reached 85%
cold; and `attempt / ensure` moved from 66.7% cold to 92.5% after one card. List completeness stayed
weak, while repeat/restore fell from 80% cold to 50% under spacing corruption. Bare-English ambiguity
recognition was poor throughout. These are model-facing development findings, not human validation or
governance evidence.
