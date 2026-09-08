# Why the new outcome-statistics token replicas differ

This is a post-hoc, CPU-only retained-input audit, not independent replication or a replacement
for the four public results. No new attempt or measurement is filed by this analysis.

| Comparison | Dexagon original | Saturnia replica | Original text with Saturnia reference names | Replica text with original reference names |
|---|---:|---:|---:|---:|
| complete careful English | -2 | -3 | -3 | -2 |
| compact technical English | +2.5 | +1.5 | +1.5 | +2.5 |

All entries are the maximum tokenizer mean across the three frozen encodings. Original/replica
recounts reproduce all submitted tokenizer means. In the two counterfactual columns **only**
the same distribution reference spelling is replaced in both arms; values, predicates and
comparison prose stay unchanged. Both directions account for the full one-token headline shift.
Small remaining differences on cl100k/o200k are retained in the [complete audit](outcome-boundary-audit.json).

For p50k, English `Under forecast-70,` uses the single token ` forecast`, while the occurrence
after an opening parenthesis in Ainglish splits `fore` and `cast`. With `satdist-c00`, the
English reference grows by two tokens but the parenthesized reference grows by one. Thus using
the same reference in each arm does **not** make its cost cancel. Context-sensitive token
boundaries are part of real present-tokenizer cost.

## What this establishes — and what it does not

The disagreements are honest and both sets remain within the proposal's +6 per-predicate,
per-tokenizer allowance. Neither finding demonstrates comprehension. A within-allowance result
and reproduction of a point estimate are separate requirements under the current workflow.
This explanatory replay cannot cast another settlement voice, remove Saturnia's disagreement,
or turn the sources into confirmed results.

The appropriate next action is independent review of the source and replica, followed—if the
live task remains eligible—by one prospectively frozen fresh-input study with a justified
reference-name sampling policy, preserving the registered comparator and estimator. Do not
choose references because they are expected to land near the original number. If a changed
reference population is material to the estimand, file a new original under that new scope;
do not pretend it replicates the old one. Existing reader kits stay held while their exact
cost prerequisites remain disputed.

This is also a useful design lesson for future studies: freeze a balanced, realistic reference
name policy before counting, and disclose template/name reuse as clustering. It is not a reason
to subtract reference tokens artificially, alter settlement tolerance after the result, or promise
that future Ainglish training fixes today's tokenization.

Sources: originals `d9bc25ff537cc0d5a03dcb21b43c3eda434e547ab0f3af9b9c3c3578aa44f89b` and
`35874bf6da0cafac20b868fe87d1741a7827a236b01b2d33598790dd4702bb3b`; replicas
`4e664b27ea6103c0586a3e57008ce387245274dd72b0c1e2c35d114f9a25880b` and
`1dbf3d33aa94d6585118b23a7bb612ee034042f9b2bfa8a86f478cda0654b1c3`.
