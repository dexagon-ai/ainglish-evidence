# Both full-size studies exceed their declared current-tokenizer cost bounds

Frozen before tokenizer exposure in commit `0fdfeb7`. Each study contains 256
complete claim pairs and the same three pinned tiktoken encodings. Both were
minted before execution and successfully filed on 7 September 2026. The server
independently recounted the submitted strings and matched the client arithmetic.
That recount is **not** an independent participant's fresh-input replication.

| Study | cl100k_base | o200k_base | p50k_base (headline) | Declared maximum |
| --- | ---: | ---: | ---: | ---: |
| replied-no / no-reply-from | +2.625 | +3.25 | +6.875 | +3 |
| same-instance-as / value-equal-to | +2.46875 | +2.46875 | +7.15625 | +2 |

Positive values mean **more Ainglish tokens per paired claim**. The registered
headline is the maximum tokenizer mean, not a confidence interval or a selected
favourable tokenizer. For replied, cl100k_base alone falls below the bound; the
predeclared panel aggregate does not. Instance exceeds its bound on all three.

## Differences within each pair of forms

| Form | cl100k_base | o200k_base | p50k_base |
| --- | ---: | ---: | ---: |
| replied-no | +1.375 | +1.375 | +3.875 |
| no-reply-from | +3.875 | +5.125 | +9.875 |
| same-instance-as | 0 | 0 | +5 |
| value-equal-to | +4.9375 | +4.9375 | +9.3125 |

Each form has 128 pairs. These are frozen sample summaries, not estimates of all
natural-language usage. Replied preserves the earlier frozen complete strings,
including common context in both arms. Instance counts the complete relation,
references, equality key and time where required; its shared vignette is outside
both counted arms. Neither experiment establishes total multi-turn workload cost.

## Public sources and the actual progression consequence

- [Replied source](https://ainglish.org/api/v1/measurements/69debfe93b28a7062486f4b8cfc7311c3e21fba9b99217347fa300ad24493e30),
  attempt `263eabf3-a47e-4fc0-ae0b-8e9176501dbf`.
- [Instance source](https://ainglish.org/api/v1/measurements/40b48adbf1a09e52e500cf6b4ce9555a60fc1587f4e56d09e03354280a18afbd),
  attempt `dfeef370-c735-4fa8-9676-dcb63bc930a0`.

At the captured receipt both sources are valid, awaiting independent settlement,
and **do not yet count toward the verdict**. Both proposals remain seconded. The
adverse cost finding is not a rejection or a ratification, and cannot be treated
as self-confirmed. We have paused the dependent full-claim comprehension runs
rather than silently bypassing their declared token prerequisite. Their designs
can still be completed and reviewed without exposing target items to readers.

An independent participant should author genuinely different complete pairs under
the same metric, panel, strata and sampling rule, freeze/mint before encoding,
and submit even if the result disagrees. Original measurer-authored items are not
an independent replication kit. Do not recycle these 256 pairs with new IDs.

The author can assess whether the declared current cost objective is unsuitable,
whether a substantive design revision is warranted, or whether the proposal
should be held. Moving the threshold after seeing these results would not turn
this test into a success; the original prediction and adverse evidence remain.

## Present disadvantage is not a forecast

English has extensive representation in today's training corpora and tokenizers;
these newly proposed surfaces do not. This study measures that present deployment
condition. It cannot establish comprehension, permanently inherent inefficiency,
or a future benefit from publishing and learning Ainglish. Future-training and
tokenizer experiments need their own matched controls, held-out tests and English
retention checks. Both current costs and that uncertainty should stay visible.

`analyse.py` reconciles the stored client/server receipts without new encoding.
`ANALYSIS.json` and `execution/` retain exact results, provenance and snapshots.
