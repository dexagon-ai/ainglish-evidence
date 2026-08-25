# Reader qualification v5: cross-vendor laboratory

This is a one-shot, construct-blind qualification screen for five model lineages. It uses only
ordinary English and never counts as evidence for an Ainglish proposal. The already-qualified
Gemma 3 reader is included as a stability anchor; Llama 3.1, Phi-4, Granite 3.3 and Command R7B
are previously untested candidates in this workspace.

The 64-item holdout is frozen and published before any candidate inference. Eight semantic axes
receive eight items each. A reader qualifies only with 64/64 exact opaque choice codes, at least
60/64 correct, at least 7/8 correct on every axis, and no hidden-thinking bytes. A scientific
roster is ready only if at least two distinct lineages qualify. Results are final regardless of
which models pass; no keys, thresholds, prompts or transport bounds are retuned after the run.

`build_spec.py` performs no model calls. `run_once.py` validates the spec digest, checks every row
against all burned qualification packets, verifies model digests and GPU residency, then runs each
reader sequentially and unloads it.

