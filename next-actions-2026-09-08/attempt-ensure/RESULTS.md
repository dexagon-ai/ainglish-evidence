# Result: an inconclusive aggregate, with a central attempt-contract failure

Filed original: https://ainglish.org/measurements/ce61ba8b9182a5b072a8dc8734f3b92f3b76829e0aff1108cd6e7086c398aaa0 . Attempt `8b2b86de-22bd-464c-a92c-37b13974688e` was minted before reader calls. The register reports the measurement valid, with no independent confirmation yet. The proposal's next action changed from needing an original to needing an independent named-original replication; its stage remains seconded.

**Do not promote the pooled number as evidence that attempt/ensure is ready.** The aggregate is +2.2175 percentage points, 95% interval [-3.0826, +7.8220]. Both improvement and harm remain compatible with this bounded sample. The original author's no-worse claim has not been demonstrated by a non-significant comparison.

| Prespecified tag group | Careful-English accuracy | Ainglish accuracy | Equal-context delta (pp) | Item-bootstrap interval |
| --- | ---: | ---: | ---: | --- |
| attempt | 75.33% | 79.09% | +3.7675 | [-5.5629, +13.7858] |
| ensure | 97.22% | 97.89% | +0.6675 | [-3.0331, +5.0000] |
| Full eight-stratum estimate | 86.27% | 88.49% | +2.2175 | [-3.0826, +7.8220] |

Tag intervals use the same official item-bootstrap method on their prespecified subsets. They are not multiplicity-corrected or template-cluster-corrected population intervals. The underlying inputs use four lexical domains and shared templates; “256 items” does not mean 256 independently sampled natural situations. Rounded arm accuracies and the delta use the official wire quantization.

## The most important result is below the headline

On the `attempt/failure-completion` probe, readers were told that the worker made a genuine adequate effort, failed and accurately reported the failure. The proposed contract says that satisfies an attempt instruction while not achieving the requested world outcome.

- Ainglish: **0 correct out of 12 observed cells**.
- Careful English: **0 out of 20**.

Neither wording communicated the gold completion distinction on this probe to either cached reader. On the related outcome-required probe, attempt scored 4/18 in Ainglish versus 6/14 in English. These are raw descriptive counts under random arm allocation, not balanced-cell experimental contrasts or a second settlement rule.

By contrast, both arms scored perfectly on retry/escalation permission, separating reported failure from actual success, and the success probe. The ensure failure-completion probe scored 15/16 in each arm. Those strong controls are useful, but they inflate an aggregate that would otherwise conceal the key attempt-contract weakness. Several tag/context estimates were negative and remain in the ledger: attempt/budget-exhausted -4.31, attempt/irreversible -1.66, ensure/retry-forbidden -3.03 points.

## Interpretation and next step

This is evidence of a failure to recover the intended distinction **in this frozen instrument**, not yet proof that the tag is inherently unsuitable. The shared failure in careful English raises a concrete question about the probe's use of “fulfilled,” the preceding requested-outcome framing and the strength of the English gloss. That possible instrument/comparator explanation is a hypothesis, not a retroactive excuse to discard the data.

The [bounded reviewer/author prompt](../prompts/attempt-ensure-review.md) asks for exact item-level scrutiny before more inference. If wording or teaching is changed, it must become a separate prospective comparison with new inputs and a clearly different exposure condition. The old zero scores stay. Bare-imperative improvement remains untested because a bare sentence must not be scored against a secret intended failure contract.

Current models' English training and tokenizer advantages matter to the longer-term strategy, but this run does not measure future training effects. It also does not establish human-reader accuracy, immediate token savings, a real action-completion benefit or independent support for ratification.

## Execution and accounting

The 48 target-independent calibration calls completed and both readers passed the frozen gate, followed by all 512 target calls. No model downloads, retries, substitutions or target resampling occurred. `execution-journal.jsonl` retains each rendered prompt, returned raw answer and per-call timestamps; the SDK retains normalized calibration and target cells. These are local execution records, not provider-signed attestations.

`cached-instrument-templates.json` publishes post-run read-only introspection of the still digest-matching cached artifacts, including their full system/template text and saved generation parameters. Both have the same fixed literal-reader system instruction; their underlying model families differ. This additional provenance was captured after the run, not falsely labelled as a new preregistration. The exact artifact digests were already pinned before inference.

The deterministic `analyze.py` replay checked all 512 target allocations/golds, exact planned/live manifest agreement, every official stratum and the complete bootstrap attestation. It reproduced the filed result and interval exactly. `execution/analysis.json` contains all tag, context, domain, reader, probe and tag/probe raw counts. Fixing the analysis filename selector to exclude the separate calibration sidecar changed no experimental input, answer or estimator.
