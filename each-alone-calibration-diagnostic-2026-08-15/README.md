# `each-alone / as-one` calibration diagnostic

Status: **frozen before diagnostic reader calls; no calls made yet**.

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
