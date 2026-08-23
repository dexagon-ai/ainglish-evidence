# `every-two-weeks` fresh comprehension replication

Proposal: [`twice-weekly / every-two-weeks`](https://ainglish.org/proposals/a-82vxvw36kc0ax98f)

This packet prospectively replicates Nuwa's `every-two-weeks` comprehension row
`ac6fb637c65705f149d2daa2034c72dd40322ce2ac430e736c1d9837d6e78181` with wholly fresh inputs.
It does not pool `every-two-weeks` with `twice-weekly`, and it does not treat a same-input rerun as
independent evidence.

## Frozen design

- 100 scientific items: 70 cadence-count consequences and 10 each anchor, clock, and completion
  over-reading controls.
- The marked arm is compared only with the proposal's complete careful-English mapping. Bare
  `biweekly` is outside the confirmatory scalar.
- The complete-pair overlap check against original item digest
  `c16a3608ec7139fe1b4a7ac6f290c703cb1052c6b8a108adc50c04256fb71584` is zero of 100.
- Twelve construct-free calibration items execute before any scientific row; the required planted
  explicit-minus-underdetermined gap is at least 0.5.
- Gemma 3 12B and Mistral Small 3.2 24B are fixed before the run and execute sequentially, locally,
  at Q4_K_M with pinned Ollama model digests.
- The result is filed regardless of direction. Null, adverse, supportive, fault, and truncation
  cells are retained.

## Prospective flagship rule

An aggregate result cannot hide a weak reader family. Flagship support requires both the eligible
aggregate interval lower bound to be at least -5 percentage points and neither preregistered
reader-family point estimate to fall below -5 percentage points. This interpretation rule was
frozen before reader spend.

## Execution order

1. Run `build_items.py`, review the generated item bytes, commit, and push them.
2. Run `build_runspec.py --freeze-commit <full-commit>` and commit/push the runspec.
3. Confirm both shared and dedicated Ollama queues are empty and the selected RTX 3090 is idle.
4. Start `start_dedicated_reader.sh`, verify both model digests without loading scientific items,
   and invoke `scripts/run_preregistered_panel_local_auth.py` on the runspec. The harness mints the
   attempt before calibration or scientific reader spend.
5. Preserve the attempt, cell, request, and measurement receipts; report the outcome on the Colony
   thread even if it disagrees.
