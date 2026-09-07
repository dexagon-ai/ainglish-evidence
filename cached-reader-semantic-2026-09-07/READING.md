# Cached reader comparison after prospective wrapper repair

Only Mistral passed the fresh neutral screen: 16/16. Qwen scored 10/16 and Gemma 4/16, below the declared 14/16 floor. Failed readers received no language cases and are not assigned a language score of zero.

The completed campaign retained 48 qualification answers and 216 target answers. All targets come from one qualified model over three authored contexts. The cases are the previously published reference-message diagnostic, deliberately reused with a different reader configuration; they are not a new independent holdout.

| Reader | Fields required | Language | Exact joint answers | Parsed under declared protocol | Truncated |
|---|---:|---|---:|---:|---:|
| mistral-small3.2:24b-instruct-2506-q4_K_M | 2 | ainglish | 0/12 | 0/12 | 0 |
| mistral-small3.2:24b-instruct-2506-q4_K_M | 2 | english | 0/12 | 0/12 | 0 |
| mistral-small3.2:24b-instruct-2506-q4_K_M | 5 | ainglish | 96/96 | 96/96 | 0 |
| mistral-small3.2:24b-instruct-2506-q4_K_M | 5 | english | 96/96 | 96/96 | 0 |

The score requires the complete requested boolean object, bare or within one permitted JSON fence, with no extra/duplicate keys or additional prose. A parser refusal is reported separately above; it must not be described as a clean semantic error. No post-hoc projection or punctuation repair changes these scores.

## Context breakdown

| Context | Fields | Language | Exact joint answers | Parsed |
|---|---:|---|---:|---:|
| handoff | 2 | ainglish | 0/4 | 0/4 |
| handoff | 2 | english | 0/4 | 0/4 |
| handoff | 5 | ainglish | 32/32 | 32/32 |
| handoff | 5 | english | 32/32 | 32/32 |
| equipment | 2 | ainglish | 0/4 | 0/4 |
| equipment | 2 | english | 0/4 | 0/4 |
| equipment | 5 | ainglish | 32/32 | 32/32 |
| equipment | 5 | english | 32/32 | 32/32 |
| community | 2 | ainglish | 0/4 | 0/4 |
| community | 2 | english | 0/4 | 0/4 |
| community | 5 | ainglish | 32/32 | 32/32 |
| community | 5 | english | 32/32 | 32/32 |

## Interruption and accounting

Another caller entered the shared service after the first three Mistral target answers. The guard stopped before the next request, with no uncertain in-flight call. The published continuation validated the exact completed prefix and reused those answers verbatim. Remaining requests used the unchanged order, prompts, model digest, CPU-only options, parser and 512-token budget. No scientific call was retried. See RECOVERY.md and the continuation receipt.

AUDIT.json reproduces the stored scores from the hash-chained raw journals and records native provider token counts. These are not reconstructed generated-token IDs, cache discounts or a monetary bill.

## What this establishes — and what it does not

This diagnoses a particular reference-assisted reader interface. The earlier strict-wrapper failures remain failures; this successor changed both the declared wrapper protocol and neutral vocabulary prospectively. The two screens do not isolate the wrapper’s causal effect.

Mistral’s qualification does not unlock the separate failed Qwen writer/reader gate, train an adapter, execute operational work, confirm a proposal or demonstrate human understanding. Three named model families were screened, but only one reached this language comparison.

These model weights and tokenizers already know English. The observed comparison concerns those current conditions, not future learned Ainglish performance or language-inherent superiority. Unqualified readers, format failures and adverse observations remain in the report.
