# Results: a brief reference helps, but neither pair clears careful-English non-inferiority

All four preregistered originals completed and were filed once on 5 September 2026. The two
existing qualified local readers made **2,048 real calls and 128 calibration calls**. Every
reader passed each positive-control block. No off-option, absent, truncated or transport-fault
cell occurred; no retry, sample substitution or model download occurred. All per-call journals,
calibration/real cell sidecars, exact requests and server readbacks are retained here.

## Registered measurements

Percentages below are equally weighted by registered form. Delta is Ainglish minus complete
careful English, in percentage points. These are four distinct originals, not replications.

| Construct and exposure | English accuracy | Ainglish accuracy | Filed delta | SDK conditional item-bootstrap 95% interval |
|---|---:|---:|---:|---|
| fact/choice, cold | 81.79% | 27.17% | −54.620 | [−61.4655, −47.0282] |
| fact/choice, brief reference | 84.11% | 59.06% | −25.055 | [−30.7724, −19.2287] |
| delegation, cold | 74.39% | 60.53% | −13.865 | [−22.0282, −5.8614] |
| delegation, brief reference | 89.84% | 85.34% | −4.500 | [−10.1284, +0.8809] |

Exact records:

- [Fact/choice cold](https://ainglish.org/measurements/cc3824df60d500a42636d7fa169f654e37843fdc848bb2d2cd011202b7997ea0), attempt `aa6c1642-46f5-456f-aece-24fd67ceb479`.
- [Fact/choice reference](https://ainglish.org/measurements/6a1b5a27b23957c2830f718974c5fcc5533701161d8b482a93bc1eaeb16f210b), attempt `b63c5f65-50bc-4830-ac41-7f769c31b6c5`.
- [Delegation cold](https://ainglish.org/measurements/2fb560cb4598a4f98f0bb177aa52d05419bc7d397569869e1cd7fdc067315b45), attempt `f77f5977-1372-473d-b1bf-1619c1f2df0e`.
- [Delegation reference](https://ainglish.org/measurements/d02307a5970cab77985aca852f41938a119b0a5e5f0882ac438dfd2ef54531cc), attempt `d02eafa8-fa3d-4026-b10c-c49e30e7b0ce`.

## The matched exposure comparison

The report-only paired contrast is `(Ainglish − English) reference − (Ainglish − English) cold`.
It keeps the same item/reader/arm cells matched between conditions and resamples 128 base-frame
clusters, preserving both forms and both readers. Analysis code and rules were committed before
calls (`d5e86dc`); inputs were already immutable at `2047023`. No new register metric is invented.

| Pair | Ainglish's own reference gain | English's own reference gain | Difference of those gains | Frame-cluster conditional 95% interval |
|---|---:|---:|---:|---|
| fact/choice | +31.89 pp | +2.33 pp | **+29.56 pp** | [+22.15, +37.33] |
| delegation | +24.81 pp | +15.45 pp | **+9.36 pp** | [+1.66, +17.13] |

This is evidence that the reference helps the marked wording relative to English **on these
fixed readers and authored held-out frames**. It is not evidence that the remaining disadvantage
has vanished. Both arms got the same bilingual guide; English benefited too, particularly for
delegation. The guide remained visible in each stateless call—there was no learned persistent
state, weight update, tokenizer adaptation, model-population sample or future-training simulation.

## Do not hide the losing form

| Form | Cold filed delta | Reference filed delta | Reference delta, report-only frame-cluster 95% interval |
|---|---:|---:|---|
| fact-not-known | −75.62 pp | −18.90 pp | [−25.18, −12.50] |
| choice-not-made | −33.62 pp | −31.21 pp | [−41.67, −21.41] |
| no-delegation | −10.81 pp | −3.72 pp | [−12.58, +4.86] |
| one-hop-delegation-allowed | −16.92 pp | −5.28 pp | [−12.16, +2.34] |

Fact/choice's aggregate improvement is mainly fact-not-known; choice-not-made's paired exposure
interval crosses zero. Neither delegation form's interval establishes the preregistered **−5 pp
non-inferiority margin**. In particular, an aggregate point of −4.5 is not a non-inferiority pass.
The per-form exposure intervals and all eight domain summaries remain in `analysis.json`.
Report-only cluster intervals supplement, and never replace, the filed SDK estimator.

Raw error classifications are retained and may overlap. In marked delegation cells, reference
exposure reduced over-restriction errors from 81 to 33, forbidden-hop errors from 11 to 1, and
transferred-accountability errors from 7 to 0. In fact/choice it reduced existence confusion
from 148 to 51 but resolution confusion only from 105 to 97. These are within-arm matched
counts, not equal-denominator comparisons between English and Ainglish.

## Overhead, limits and next decision

- Fact/choice guide: 150 words, 188 / 184 / 206 tokens under cached cl100k / o200k / p50k.
- Delegation guide: 140 words, 183 / 185 / 200 reference-encoding tokens.
- That overhead is repeated per reference call in both arms. It is not amortised, not measured
  in the local models' native tokenizer and not a billing claim. UTF-8 byte counts are retained.
- Two fixed Q4 lineages and repeated templates over eight domains limit generalisation. The
  two exposure orders are counterbalanced between constructs, not a full control for time.
- These tests cover the core joint distinctions, not every normative fidelity, authority,
  robustness, translation, human comprehension or post-ratification-use requirement.
- Existing cold/adverse/reference originals remain visible and unchanged. Current ratification
  stays separate from evidence confirmation; these five new measurements (including the separate
  verdict token original) create no independent confirmation or new ratification by themselves.

Next useful evidence is independent semantic/design assessment followed, if justified, by a
fresh-case matched replication using a separately qualified reader setup. Do not rerun these
same cases until the remaining loss disappears. For ordinary website teaching, the distinctions
can be explained clearly while saying that this study found exposure benefits but not established
non-inferiority. Future training potential remains plausible and unmeasured, not waived into fact.
