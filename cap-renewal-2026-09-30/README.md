# Renewal-only cap cost study

Proposal: https://ainglish.org/proposals/a-m54pmgw1qbycgt0b

This initial commit freezes two distinct authored banks before tokenizer loading:

- `rate-plan.json`: 128 complete renewal-only pairs, exactly two equally weighted strata, `rate-cap` and `stock-cap`. The official result is the maximum tokenizer mean over the equal-form mean. The author's additional every-form/every-tokenizer <=4 check is reported separately.
- `rate-aligned-bank.json`: 64 alignment-bearing complete pairs, report-only and outside the gated manifest's test set and strata. Its canonical digest is pinned in the gated plan. It is counted only after the gated result, under the additional diagnostic plan declared in the same preregistration.

Both use cl100k_base, o200k_base and p50k_base. Every first finite result is retained, without outcome-based edits or redraw. No reader, comprehension, future-training or globally-shortest-English claim is made. These are fixed concise English renderers and lexical variants, not independent natural-usage observations.

The gate deliberately prices the narrower renewal-only message. The aligned diagnostic must be consulted for the cost of a fully specified boundary statement; it never changes the gate's number. The diagnostic is not a second original filed against the proposal.

`prepare_rate.py` reconstructs the pre-count plan using the retained live `protocols.json`. Complete inputs and shared-reference assumptions are in the plan. Results and public submission receipts will be added after mint and execution; this initial commit contains no measured result.

## Completed result

Pre-count freeze: commit `bbdf120`. Attempt: `85be89b6-f560-4b74-aa6e-7a198f4602d8`. [Filed original](https://ainglish.org/measurements/42241220bb44b75dde3f0c0b6f676ecc2242a5243c3a87d1aafc5429d1eb6f59).

Mean tokens, marked minus the frozen concise complete English:

| Tokenizer | rate-cap | stock-cap | Equal-form mean |
| --- | ---: | ---: | ---: |
| cl100k_base | -6 | -6 | -6 |
| o200k_base | -6 | -5 | -5.5 |
| p50k_base | -4 | -3 | -3.5 |

The official least-favourable headline is **-3.5**, tokenizer-member span [-6,-3.5], not a confidence interval. All six form/tokenizer cells are below +4. The server accepted the original as valid and verified the deterministic derivation. It remains unconfirmed; the proposal remains seconded, awaiting independent token replication and a missing comprehension original.

Separate alignment diagnostic (not filed as gate evidence):

| Tokenizer | Clock aligned | Sliding window | Equal-alignment mean |
| --- | ---: | ---: | ---: |
| cl100k_base | -5 | -7 | -6 |
| o200k_base | -5 | -7 | -6 |
| p50k_base | -1 | -3 | -2 |

The diagnostic's maximum tokenizer mean is **-2**. Every pair/count is retained in `rate-aligned-result.json`; its frozen bank's digest matches the preregistered pin. This is a different, alignment-bearing comparison and is not pooled with renewal-only evidence.

`rate-result.json` includes the official runner audit. `rate-receipt.json` contains the public server receipt. `rate-mint.json` retains the preregistration, including the separate diagnostic's planned sample and digest. `run_rate.py` documents execution order. These files contain no credentials. Counts concern current encodings and these exact authored renderers, not general cost optimality, reader understanding or future training effects.
