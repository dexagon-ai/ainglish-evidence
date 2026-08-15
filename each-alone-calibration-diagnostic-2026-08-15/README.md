# `each-alone / as-one` calibration diagnostic

Status: **completed once on GPU 0; semantic failure isolated; not proposal evidence**.

This is a post-abort, construct-free diagnostic of Ainglish attempt
`c4ddce0b-eac5-46b4-b1ec-b391e62516cc`. That attempt's positive-control aggregate was 7/12 on
the explicit-count arm and 6/12 on the ambiguous arm, below its frozen competence threshold. Its
receipt did not retain calibration answers, so it cannot distinguish semantic errors from
off-option formatting.

This diagnostic asks only the same six generic positive controls. It does **not** load or ask any
of Rosetta's 19 scientific `each-alone / as-one` rows. It uses the same readers, prompt template,
temperature, token bound, endpoint style, arm order and exact-label parser as Ainglish 0.2.29, but
retains each raw response alongside its parsed label.

The diagnostic is not an Ainglish measurement, replication, successor attempt, or evidence for
or against the proposed markers. Its only purpose is to locate the failed competence check. No
result from it may be reported as proposal evidence, and no calibration set should be selected
merely because this post-hoc run makes it pass.

Execution is restricted to a disposable loopback-only Ollama service on RTX 3090 GPU 0, with one
loaded model and one request at a time. There is no CPU fallback. The runner refuses before its
first call unless GPU 0 has at least 20,000 MiB free, the shared Ollama service has no resident
model, the dedicated service has no resident model, and the diagnostic result path does not
already exist.

`diagnostic-spec.json` is the frozen input. Its canonical JSON SHA-256 is
`60464254168d3787f7630b996bbbde07964ca0390fa57c92965e13a627b9c58c`.
`run_diagnostic.py` records raw outputs without retrying or changing the prompt.

## Result

The frozen diagnostic ran once under Ainglish 0.2.29 on the same two model artifacts. The
disposable service identified host GPU 0 (`00000000:24:00.0`) as an RTX 3090 CUDA 8.6 device;
immediately before the run it had 24,308 MiB free. The service was stopped after capture.

Every one of the 24 responses was a live, non-truncated, exact permitted option. There were zero
off-option outputs. The original aggregate was reproduced exactly:

| Reader | Ambiguous arm | Explicit-count arm |
|---|---:|---:|
| Gemma 3 12B Q4_K_M | 3/6 | 3/6 |
| Qwen 2.5 7B Q4_K_M | 3/6 | 4/6 |
| **Pooled** | **6/12** | **7/12** |

The answer-class split locates the semantic failure:

| Explicit-count class | Gemma 3 | Qwen 2.5 | Pooled |
|---|---:|---:|---:|
| `three separate` | 3/3 | 3/3 | 6/6 |
| `one joint` | 0/3 | 1/3 | 1/6 |

The readers generally answered from the plural subject (“the three agents”) even when the next
sentence explicitly stated that exactly one joint event occurred. The prompt transport and exact
label parser behaved as declared; weakening the threshold or accepting more output forms would
not cure this failure. These two reader artifacts should not be reused together for a successor
that claims to measure plural event-count comprehension.

`diagnostic-results.json` contains every raw output. Its canonical JSON SHA-256 is
`1845b11b37aa9dc0b3f1af9756a612c0337691655c6b97d03412bee646178bcc`; its on-disk SHA-256,
including formatting and the trailing newline, is
`2e33c4b583bbf63856180fca847cfe0348e01bd91abf15746accc42e932a7433`.

## Clean successor boundary

A successor should keep the failed attempt and this diagnostic visible, retain the `0.5`
competence floor, and use readers first screened only on this now-development control set. Its
actual calibration rows must then be newly authored and held out until after the successor is
minted. The held-out bank should balance explicit `one`, explicit `three`, and ambiguity-aware
answers so a reader cannot pass by copying the grammatical subject's number. The 19 scientific
rows may remain untouched and unseen during reader screening.
