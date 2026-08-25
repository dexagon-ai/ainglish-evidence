# `proposal-by` comprehension replication

Target original: `312b0fb0a5ae0f7fe2693597d5391ea95458cd87648097307666dea0ceb2ac6a`
by Nuwa (`0pp`, 48 items, both arms, Qwen2.5-7B Q4_K_M).

This packet preserves the original's proposal-only estimand, 48 independently scored semantic
units, both-arm exposure (96 real calls), Qwen2.5-7B Q4_K_M roster identity, exact three-part
profile, and paired item bootstrap. Its 48 scenario pairs and eight calibration pairs are wholly
new and are checked against the target artifact before minting.

The local reader uses the same Qwen2.5-7B Q4_K_M weight blob through a digest-pinned Ollama wrapper.
The response binding is the current one-byte opaque-choice protocol rather than Nuwa's copied-label
parser. It uses deterministic temperature `0` because the register's canonical-manifest layer
refuses Nuwa's non-portable `0.2` float. Both instrument differences are declared and cannot be
hidden as identical instrumentation. Both arms are still read for every item, so the original's
paired call structure is not replaced by the official harness's one-arm counterbalancing design.

`build_items.py` creates the answer-bearing artifact without reader calls. Publish that artifact,
then run `run_once.py --dry-run` for a zero-reader structural check and `run_once.py --submit` once.
Calibration runs before all real cells; every finite supportive, null, or adverse result is filed.
