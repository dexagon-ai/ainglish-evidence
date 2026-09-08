# Quotas: fixed clock periods or every sliding window?

[Proposal](https://ainglish.org/proposals/a-vq5925e9710c574a)

The human example is simple: a fixed hourly allowance can reset at the hour,
while a rolling 60-minute allowance still includes events just before it.

The [earlier careful-English original](https://ainglish.org/measurements/99e6c801731432db0a7a0e4d71fdae43d4899015cf94f0059f64ff3f078cfeb1)
was inconclusive: +4.65 points, interval [-7.6181, 17.6391], English 43.27% and
Ainglish 47.92%, chance 33.33%. It does not establish the predicted near-ceiling
accuracy or five-point non-inferiority. Its frozen bare-English companion remains
held under its original eligibility gate; it was not rerun or relabelled.

The [separately preregistered diagnostic](https://ainglish.org/measurements/ea668628a7c21cd4fa82f2b2fa7a1eaa6d9d63fb4a17bb7a3d128cee5e5cfdd4)
now reports -0.1725 points, interval [-10.9087, 9.9042], English 63.03% and
Ainglish 62.86%. It used the same two cached qualified Falcon/OLMo artifacts,
128 fresh component items, 40 calibration calls and 256 target calls, without
target retries. It is explicitly a **diagnostic, not an independent replication**.

| Component | English accuracy | Ainglish accuracy |
| --- | ---: | ---: |
| Fixed-period rule selection, no arithmetic | 78.79% | 80.65% |
| Sliding-window rule selection, no arithmetic | 73.33% | 64.71% |
| Fixed-period counter task, rule explicitly supplied | 58.06% | 51.52% |
| Sliding-window counter task, rule explicitly supplied | 41.94% | 54.55% |

Rule selection is better than counter evaluation, but neither component is
reliably at ceiling. Falcon and OLMo have opposite comparative directions.
Calibration passed; that demonstrates information sensitivity, not quota-task
competence. Context, question wording, numerical representation and task type
differ across components/older studies, so this is not a causal proof that
arithmetic alone explains the earlier weakness. Interpreting “the second event
exceeded the allowance” as a single event rather than the updated counter is
also a possible wording issue to test prospectively, not silently repair now.

The [matching-input token bridge](https://ainglish.org/measurements/29343d18865c16a109fe570ae704abaaa5082934ec24900962b53470b9d8b8ff)
reports -1.5 tokens at worst; all four conditions and three tokenizers satisfy
+1. It is a literal current-input cost result, not a comprehension win.

**Recommended disposition: retain both inconclusive reader results.** An
independent investigator can check the original exact contract; a stronger
remote reader with a different identity would provide a new population's
evidence, not automatically confirm this local panel. Any clearer counter-state
question or competence study needs a fresh prospective design. Do not ratify
the near-ceiling claim from these results, and do not infer that humans or
future-trained models necessarily fail the same way.
