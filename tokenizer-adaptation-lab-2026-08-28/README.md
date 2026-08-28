# Tokenizer adaptation lab

This matched-budget experiment asks a narrow question: if a tokenizer is actually trained with
Ainglish surfaces, can it allocate vocabulary differently without changing the model weights?
It crosses two vocabulary sizes, two pre-tokenization policies, and careful-English versus
Ainglish exposure. Every cell receives 8 MB of the same filtered public English corpus plus a
2 MB supplement; both supplements repeat each of the 57 semantic pairs exactly 32 times and use
neutral filler to equalize bytes.

| Vocab | Hyphen policy | Ainglish-token change | English-token change | Ordinary-eval change | Marker-token change | Single-token markers |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 8000 | `punctuation_split` | -94 | +122 | -164 | -7 | +0 |
| 8000 | `whitespace_only` | -368 | +182 | +364 | -46 | +10 |
| 16000 | `punctuation_split` | -93 | +83 | -23 | -3 | +0 |
| 16000 | `whitespace_only` | -585 | +267 | +237 | -49 | +16 |

Negative token changes mean the Ainglish-exposed tokenizer used fewer tokens than its matched
careful-English control. The ordinary-evaluation column is the corresponding cost or benefit on
2 MB of held-out public English. The two hyphen policies are deliberately reported separately:
vocabulary exposure cannot create a whole-marker token when the pre-tokenizer forbids merges
across hyphens.

This is not a claim about any laboratory's eventual production tokenizer. It demonstrates a
mechanism and its trade-off under small, reproducible tokenizers. Model exposure and tokenizer
adaptation remain different interventions.

Frozen report digest: `a1725803b5af686cc46ef84ea1e6ce90a39d4cc3524c11c7da248518217ded15`.
