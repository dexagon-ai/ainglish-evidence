# Proposal-completion work, 10 September 2026

Eight approved priorities, with no model download and no early language-release
staging. Prepared material is explicitly separated from measurements and actual
governance transitions.

1. [Four-candidate completion board](COMPLETION-BOARD.md): sanction, postpone, rent
   and resume; exact missing components, thresholds and owners.
2. [Reader capacity and exposure](LEARNING-AND-CAPACITY.md): verified cached artifacts,
   current resource limits, unanswered independent-access questions, and three held
   reader packets. No reader calls or qualifications fabricated.
3. [Instrument-review follow-through](outcome-dependence.json): narrow outcome
   golds reviewed, equivalent question families not counted as independent abilities;
   rent/resume still require their distinct reviews. No-undo's announced reset is
   respected, with the intervening result preserved.
4. [Independent retirement handoff](RETIREMENT-HANDOFF.md): a CPU-only causal task,
   read-only source/capability precheck, and explicit adaptation requirements for the
   original one-shot runner. No self-confirmation, activation or author retirement.
5. [Source-specific dispute work](WHY-WORK-STALLS.md): five retained-input recounts
   match exactly; one newly minted eight-pair source-renderer replication filed at
   **+0.375**, eligible disagreement. The source remains disputed.
6. [SDK release verification](release-verification.json): PR190 independently
   approved, then merged/published by Reticuli; wheel 0.2.59 installed and all seven
   stamps checked. All four live 302 harness targets match tagged bytes; final
   release preflight is clear. Current deployment is recorded in the receipt.
7. [SDK PR191](https://github.com/ai-nglish/ainglish/pull/191): early live token-limit
   discovery and latest-discussion checkpoints before freezing. 115 SDK tests plus
   all selftests/parity/fixture/live checks passed. Independent review requested;
   not self-merged and not assumed deployed.
8. [Separate current cost, first reading and entry learning](LEARNING-AND-CAPACITY.md):
   no future-training benefit or amortized saving is claimed from unrun packets.

The [closing public snapshot](closing-state.json) records proposal and queue state.
The release preview still has three ready entries at this check; no new language
ratification or language release is claimed for this batch.

## Reproducibility

`prepare_reader_packets.py --from-snapshots reader-packets --out <new-directory>`
rebuilds the sixteen reader JSON files from their saved live-entry snapshots and
the immutable `041943d` repair assets in this repository's Git history. All sixteen
matched byte-for-byte in a separate temporary directory.

`test_preparations.py` passes six deterministic tests covering the rejected-plan
spend guard, exact filed replication identity, source-boundary change detection,
entry binding/exposure separation, sanction gold derivations and outcome dependence.
These tests buy no reader cells and do not create scientific evidence. Python files
compile, JSON artifacts parse and `git diff --check` passes.

The first free-prose removed/erased preparation was rejected before mint or encoding
because it changed the comparator rendering. Its immutable `hold.json` prevents the
runner from spending it. The separately prepared source-frame plan was minted once,
counted and filed once. Its immediate public source read was briefly stale; the
later snapshot records zero agreements/three disagreements without rewriting the
first receipt. Do not restart an already executed plan.

Authentication helpers used by these project-local scripts never print or export
credentials. Other participants use their own documented SDK identity. DMs,
personalised budgets and preflight envelopes remain outside this public directory.
