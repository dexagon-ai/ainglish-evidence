# Flagship cold-clarity atlas result

Status: **complete**

All 180 frozen calls expanded to 1440 scored cells. Invalid batches: **17**. No model was downloaded and no inference call was retried.

Raw response content digest: `ba296093f4ed2f65406461f52d5955a831fde6e6449d8e6203cc205252f9f5c9`. Analysis content digest: `689fad946c156989c5f80738c2b8e6d19717426b437be80af15871b0934d51aa`.

## Model results

| Installed model | Cold | One card | Careful English | Bare ambiguity | Corrupted |
|---|---:|---:|---:|---:|---:|
| `qwen3.6:35b` | 79.2% | 33.3% | 77.1% | 27.1% | 72.9% |
| `gemma3:12b` | 60.4% | 85.4% | 66.7% | 39.6% | 60.4% |
| `mistral-small3.2:24b-instruct-2506-q4_K_M` | 91.7% | 100.0% | 100.0% | 47.9% | 93.8% |
| `phi4:14b` | 100.0% | 83.3% | 95.8% | 25.0% | 81.2% |
| `olmo2:13b` | 60.4% | 75.0% | 68.8% | 41.7% | 52.1% |
| `lfm2:24b` | 39.6% | 64.6% | 47.9% | 29.2% | 45.8% |

## Prospective development classification

| Construct | Class | Cold | One card | Careful | Bare | Corrupted | Defined-cold | Corrupt-cold | Flags |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| among-others / and-no-others — is the list the whole list? | `amendment_candidate` | 68.8% | 64.6% | 70.8% | 39.6% | 70.8% | -0.042 | +0.021 | bare_ambiguity_failure, reader_heterogeneity, invalid_channel |
| one-or-more(<role>) / exactly-one(<role>) — does ‘a reviewer’ require at least one participant or exactly one? | `amendment_candidate` | 77.1% | 100.0% | 75.0% | 18.8% | 72.9% | +0.229 | -0.042 | definition_gain, bare_ambiguity_failure, reader_heterogeneity, invalid_channel |
| repeat-event / restore-state — did ‘again’ repeat the action, or only bring the result back? | `amendment_candidate` | 66.7% | 41.7% | 60.4% | 35.4% | 41.7% | -0.250 | -0.250 | corruption_drop, bare_ambiguity_failure, reader_heterogeneity, invalid_channel |
| they-one / they-many — say whether ‘they’ is one actor or several | `amendment_candidate` | 81.2% | 83.3% | 77.1% | 37.5% | 70.8% | +0.021 | -0.104 | bare_ambiguity_failure, reader_heterogeneity, invalid_channel |
| observed / reported(<by>) / inferred(<from>) - mark where a claim came from | `amendment_candidate` | 70.8% | 75.0% | 81.2% | 25.0% | 68.8% | +0.042 | -0.021 | cold_careful_gap, bare_ambiguity_failure, reader_heterogeneity, invalid_channel |
| attempt: / ensure: — say whether the instruction tolerates failure | `amendment_candidate` | 66.7% | 77.1% | 91.7% | 54.2% | 81.2% | +0.104 | +0.146 | cold_careful_gap, definition_gain, bare_ambiguity_failure, reader_heterogeneity, invalid_channel |

## Descriptive channel sensitivity

This post-result view removes entire invalid batches only to distinguish channel failures from
parseable semantic choices. It does **not** replace the preregistered classifications above; invalid
batches remain failures in every primary denominator.

Seven invalid calls were Ollama HTTP 500 responses from Qwen 3.6 35B under concurrent residency. Ten
were strict output-contract failures: one Phi batch, four OLMo pronoun batches, and five LFM batches.

| Construct | Cold | One card | Careful | Bare | Corrupted |
|---|---:|---:|---:|---:|---:|
| among-others / and-no-others | 68.8% (33/48) | 77.5% (31/40) | 70.8% (34/48) | 39.6% (19/48) | 70.8% (34/48) |
| one-or-more / exactly-one | 77.1% (37/48) | 100.0% (48/48) | 90.0% (36/40) | 18.8% (9/48) | 72.9% (35/48) |
| repeat-event / restore-state | 80.0% (32/40) | 62.5% (20/32) | 72.5% (29/40) | 42.5% (17/40) | 50.0% (20/40) |
| they-one / they-many | 97.5% (39/40) | 100.0% (40/40) | 92.5% (37/40) | 37.5% (18/48) | 85.0% (34/40) |
| observed / reported / inferred | 85.0% (34/40) | 90.0% (36/40) | 97.5% (39/40) | 25.0% (12/48) | 82.5% (33/40) |
| attempt / ensure | 66.7% (32/48) | 92.5% (37/40) | 91.7% (44/48) | 54.2% (26/48) | 81.2% (39/48) |

The clearest current candidate is pronoun number. Role cardinality and the failure contract show a
large one-card accommodation effect. Claim-source is usable but still trails careful English.
Repeat/restore is genuinely fragile: its one-card and corruption results remain weak even after
channel failures are removed. List completeness is heterogeneous and does not earn a positive
development label on this battery.

## Interpretation boundary

These classifications answer a narrow model-facing development question. They do not establish how ordinary humans understand the forms, provide independent settlement voices, or change any proposal's lifecycle state.

The one-card condition is immediate accommodation, not proof that a model was trained on Ainglish. Current models and tokenizers inherit an English training advantage; a cold Ainglish loss is an honest present-state result, while future pretraining benefits remain unproven.

Every failed cell and channel error remains in `analysis.json`; no adverse result is discarded.
