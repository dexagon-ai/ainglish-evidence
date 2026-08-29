# Post-hoc benchmark robustness audit

Status: **complete**

This deterministic audit reuses the frozen 2,904-cell benchmark. It made no model calls and treats readers or manually grouped lineages—not individual cells—as the descriptive units.

## Main comparison

| Comparison | Track | Reader mean | Equal-lineage mean | 95% descriptive bootstrap interval | Lineage + / 0 / - | Exact sign probability | Leave-one-lineage-out range |
|---|---|---:|---:|---:|---:|---:|---:|
| ainglish_minus_careful | cold | -0.136364 | -0.116883 | [-0.159497, -0.073864] | 0 / 4 / 12 | +0.000488 | [-0.124675, -0.106494] |
| ainglish_minus_careful | one_exposure | -0.035124 | -0.036120 | [-0.085227, +0.014205] | 5 / 3 / 8 | +0.581055 | [-0.050649, -0.026407] |
| ainglish_minus_bare | cold | +0.074380 | +0.051136 | [+0.008523, +0.099432] | 8 / 6 / 2 | +0.109375 | [+0.036364, +0.060606] |
| ainglish_minus_bare | one_exposure | +0.165289 | +0.117695 | [+0.068182, +0.167208] | 13 / 2 / 1 | +0.001831 | [+0.106061, +0.131602] |

The bootstrap interval and exact sign probability are post-hoc descriptive stability summaries over 16 manually declared lineages. They are not population-level inference: the lineages are a convenience roster and may share training data or ancestry.

## Prompt-local definition effect

| Comparison | Reader mean change | Equal-lineage mean change | 95% descriptive bootstrap interval | Lineage + / 0 / - |
|---|---:|---:|---:|---:|
| ainglish_minus_careful | +0.101240 | +0.080763 | [+0.048296, +0.114448] | 12 / 4 / 0 |
| ainglish_minus_bare | +0.090909 | +0.066558 | [+0.028409, +0.104707] | 11 / 4 / 1 |

A positive change means the Ainglish arm improved relative to that comparator after one supplied definition. This is prompt exposure, not pretraining or tokenizer integration.

## Operational-pathology sensitivity

| Comparison | Track | Equal-lineage mean, all 16 | Mean excluding DeepSeek and Solar | Remaining lineages |
|---|---|---:|---:|---:|
| ainglish_minus_careful | cold | -0.116883 | -0.133581 | 14 |
| ainglish_minus_careful | one_exposure | -0.036120 | -0.044527 | 14 |
| ainglish_minus_bare | cold | +0.051136 | +0.058442 | 14 |
| ainglish_minus_bare | one_exposure | +0.117695 | +0.131262 | 14 |

This exclusion is not a replacement result. Solar's all-HTTP-500 rows and DeepSeek's strict-schema failures remain in the frozen primary result.

## Construct heterogeneity: Ainglish minus careful English

| Construct | Cold equal-lineage mean | One-exposure equal-lineage mean | Exposure change |
|---|---:|---:|---:|
| or-both / not-both | +0.053571 | +0.066964 | +0.013393 |
| no-delegation / one-hop-delegation-allowed | -0.040179 | +0.004464 | +0.044643 |
| each-alone / as-one | -0.071429 | +0.062500 | +0.133929 |
| stopped / done-under / complete-for | -0.071429 | +0.053571 | +0.125000 |
| text-fixed / meaning-fixed | -0.093750 | -0.125000 | -0.031250 |
| we-including-you / we-excluding-you | -0.093750 | +0.000000 | +0.093750 |
| you-one / you-all | -0.093750 | -0.062500 | +0.031250 |
| by-unknown / by-withheld | -0.102679 | +0.071429 | +0.174107 |
| start-by / complete-by | -0.120536 | +0.026786 | +0.147321 |
| fact-not-known / choice-not-made | -0.174107 | -0.058036 | +0.116071 |
| true-as-worded / false-as-worded | -0.477679 | -0.437500 | +0.040179 |

Each construct has only two frozen items per reader. The ranking is diagnostic and must not be presented as independent confirmation of any construct.

## Bottom line

Equal-lineage weighting and leave-one-lineage-out checks do not change the qualitative result: prompt-cold Ainglish trails careful explicit English, beats bare ambiguous English, and one supplied definition narrows the careful-English gap while widening the bare-English advantage. The construct table shows where that aggregate story is weakest and strongest.

Nothing here establishes current token efficiency, future-training efficiency, human intuitiveness, external adoption, model-family independence, or governance eligibility.
