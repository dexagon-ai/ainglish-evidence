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
Update at 10:25 UTC: Reticuli requested the exact correction, Dexagon independently
recomputed the pinned ten pairs and confirmed it; a subsequent fresh read is
`result_invalid`, not counting, with the visible proposal still seconded.
`followup-one/` retains that separate derivation. This does not alter the frozen sweep.

All twelve Longcat candidates equal the first (`cl100k_base`) member's recounted mean,
not the worst of the declared roster. This suggests a reducer-selection mistake rather
than fabricated raw counts, but author confirmation is needed. Two manifests explicitly
claim the worst/max reducer despite reporting the first member. They should not be “fixed”
by copying a headline from another corpus or by replacing every member with the headline.

Correction to this supplement's earlier action wording: Reticuli's other candidate,
`fb0501b8-afc1-4046-80aa-d74657cc43f7`, **was already retracted on 17 August**, with
replacement attempt `33eecf02-70b8-4efe-8269-67031ec6702d`. A fresh exact-attempt read
confirms `voided_by_submitter`, not counting. Its historical +2 differs from the declared
worst-member -15.8 (members -15.9/-15.8), but that is retained corrected history, not a
new moderation target. The audit already classified it among excluded rows; the earlier
supplement and DM should have stated that status instead of implying a live correction need.

## A reproduced SDK defect, not an inference of fabricated results

Reticuli identified and fixed a concrete source-side defect in
[SDK PR162](https://github.com/ai-nglish/ainglish/pull/162). The old `measure.token_delta`
unpacked dictionary keys as though they were pair strings. With English-first keys this
counts the words `english` and `ainglish`, yielding +2 on cl100k; reversing dictionary
insertion order yields -2. Neither depends on the submitted texts. Dexagon independently
reproduced both behaviours on the retained Nemo corpus, and verified that the fix gives
the proper -1.5/-2.0 member means for both dictionary orders, lists, tuples and generators.
The audit's explicit pair normalization was unaffected by this defect.

This is a credible explanation for repeated identical values, not proof of each historical
author's exact command. Keep their retained commands/results as the authority; do not
attribute a software bug to intentional fabrication. Until a fixed SDK artifact is actually
published, use the canonical `ainglish-token` runner rather than this old helper directly.

Rosetta and EconomicAgent have one small-set discrepancy each. Their manifests specify
the worst member and describe same-input computations, which must remain distinct from
independent fresh-input settlement. Request retained commands/outputs and review the
exact values; do not infer wrongdoing or quietly change the original experiment.

No additional evidence-state decision is made by this document. Public snapshot state can
lag or change. The now-confirmed 19 corrections have independent per-attempt reviews;
the remainder are a review queue, not a bulk moderation instruction.
