# Traffic-weighted token economics

This report prices every reviewed pair in the CC0 Ainglish v0.35.0 training pack under
three fixed current tokenizer families, then shows both equal-weight and observed-use-weighted
views. A negative delta means the Ainglish form uses fewer tokens than its complete careful-
English comparator. The observed-use view is a coverage-limited proxy, not a universal traffic
forecast.

| Tokenizer | Equal pairs | Equal constructs | Observed-use weighted | Supportive pairs |
| --- | ---: | ---: | ---: | ---: |
| `cl100k_base` | -10.140 | -11.601 | -15.993 | 89.5% |
| `o200k_base` | -10.035 | -11.504 | -15.558 | 89.5% |
| `p50k_base` | -7.807 | -8.974 | -13.234 | 87.7% |

Traffic receipt: **281** recent semantic uses across **17** positively weighted constructs; **19/19** released constructs had current post-ratification coverage.

## What this can and cannot say

The equal-pair view describes the 57 reviewed examples. The construct-equal view prevents
constructs with more examples from dominating. The traffic proxy asks what those per-construct
means would imply if recent semantic-use counts were representative. It does not claim that the
reviewed example is the sentence actually observed in traffic.

These are current literal-token receipts. A model trained on Ainglish can reduce definitions,
retries, repairs, and explanation overhead without changing a single token count here. Literal
counts for the same string change only when the tokenizer or the string changes; that is tested
separately in the tokenizer-adaptation lab.

Frozen report digest: `e0aa1036a02728a98199f3bd3bc3a923a36ffcbcc011f74d8db77dcd1ba3800f`.
