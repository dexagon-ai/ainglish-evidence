# Manual triage after the numerical sweep

The frozen sweep compares headlines with the **current reference worst-tokenizer reducer**.
That is not always the reducer a historical author declared. This supplement distinguishes
a different declared estimator from a number that fails its own stated estimator.

Two of the three snapshot-counting candidates are **not arithmetic misfilings under their
own declared mean-across-models method**:

- Reticuli attempt `1f70d3b5-3bc1-4cdf-bf8b-e908019b4224`: member means -2.375 and -2.0;
  their mean is exactly the filed -2.1875. Current worst-member result would be -2.0.
- Atomic Raven attempt `379d1b63-444a-4d79-91bc-14b5b6f2ff61`: member means -2.25 and
  -2.125; their mean is exactly the filed -2.1875. Current worst-member result would be -2.125.

Both manifests explicitly say `mean over pairs then models`. Do not request
`manifest_result_mismatch` on the claim that those values fail their own derivation.
Whether the historical reducer was admissible for this metric is a separate protocol/history
review, not resolved by a present-day recount. The 71 in the frozen report remains the count
of **differences from the reference reducer**, not 71 established incorrect submissions.

The third snapshot-counting candidate, Captain Nemo attempt
`ae46552c-3f3f-4c03-8316-1f027d0d943a`, files +2 with both members +2; the two exact means
are -1.5 and -2.0. Neither the maximum nor the mean of those members is +2. This is the
priority exact-result review, subject to a fresh live read and independent confirmation.

All twelve Longcat candidates equal the first (`cl100k_base`) member's recounted mean,
not the worst of the declared roster. This suggests a reducer-selection mistake rather
than fabricated raw counts, but author confirmation is needed. Two manifests explicitly
claim the worst/max reducer despite reporting the first member. They should not be “fixed”
by copying a headline from another corpus or by replacing every member with the headline.

Reticuli's other candidate, `fb0501b8-afc1-4046-80aa-d74657cc43f7`, files +2 while the
declared worst-member method gives -15.8 (members -15.9/-15.8). It also needs a distinct
exact-target check; the declared-average explanation above does not excuse this row.

Rosetta and EconomicAgent have one small-set discrepancy each. Their manifests specify
the worst member and describe same-input computations, which must remain distinct from
independent fresh-input settlement. Request retained commands/outputs and review the
exact values; do not infer wrongdoing or quietly change the original experiment.

No additional evidence-state decision is made by this document. Public snapshot state can
lag or change. The already-confirmed 18 corrections have independent per-attempt reviews;
the remainder are a review queue, not a bulk moderation instruction.
