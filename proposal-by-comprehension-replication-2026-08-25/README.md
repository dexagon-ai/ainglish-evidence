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
The attempt manifest uses the published immutable URL plus the canonical item-array SHA rather than
inlining the bulky packet, as required by the register's 20 KB manifest ceiling.

## Outcome

Attempt `9f7e47e2-14fe-4b2a-be9f-67f46c3eb6e4` aborted before any scientific cell. The Qwen reader
answered seven of eight deliberately uninformative English calibration arms as if they were
offers, producing English `0.875`, planted Ainglish `1.0`, and a gap of only `0.125` against the
frozen `0.5` minimum. All 16 calibration cells are retained. The runner's first abort request used
an obsolete gate-kind label; the fail-safe then closed the attempt as `harness_error`. No threshold,
item, prompt, reader, or outcome was retuned and this packet must not be rerun.
