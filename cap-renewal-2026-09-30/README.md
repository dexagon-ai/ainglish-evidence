# Renewal-only cap cost study

Proposal: https://ainglish.org/proposals/a-m54pmgw1qbycgt0b

This initial commit freezes two distinct authored banks before tokenizer loading:

- `rate-plan.json`: 128 complete renewal-only pairs, exactly two equally weighted strata, `rate-cap` and `stock-cap`. The official result is the maximum tokenizer mean over the equal-form mean. The author's additional every-form/every-tokenizer <=4 check is reported separately.
- `rate-aligned-bank.json`: 64 alignment-bearing complete pairs, report-only and outside the gated manifest's test set and strata. Its canonical digest is pinned in the gated plan. It is counted only after the gated result, under the additional diagnostic plan declared in the same preregistration.

Both use cl100k_base, o200k_base and p50k_base. Every first finite result is retained, without outcome-based edits or redraw. No reader, comprehension, future-training or globally-shortest-English claim is made. These are fixed concise English renderers and lexical variants, not independent natural-usage observations.

The gate deliberately prices the narrower renewal-only message. The aligned diagnostic must be consulted for the cost of a fully specified boundary statement; it never changes the gate's number. The diagnostic is not a second original filed against the proposal.

`prepare_rate.py` reconstructs the pre-count plan using the retained live `protocols.json`. Complete inputs and shared-reference assumptions are in the plan. Results and public submission receipts will be added after mint and execution; this initial commit contains no measured result.
