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
- Seed `2026082309` deals exactly 100 scientific cells to each arm. Effective panel size is
  conservatively declared as one on the reader axis rather than inferred from the two-name roster.
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

## Completed result

- Attempt: `af756bfe-63a3-4b86-a1ae-9f2bc2a966f5`
- Measurement: `111624f17422edf530e8ed90cee07c04edef3e0a880514e73ab33e7b5a4e9cf2`
- Target: `ac6fb637c65705f149d2daa2034c72dd40322ce2ac430e736c1d9837d6e78181`
- Headline: **+3.00 percentage points**, interval **[-10.8411, +16.5276]**
- Absolute accuracy: marked **37/100 (37%)**; careful English **34/100 (34%)**
- Reader strata: Gemma **+1.36 pp**; Mistral **+4.52 pp**
- Calibration: explicit **1.00**, underdetermined **0.00**, gap **1.00**; passed
- Yield: **248/248** cells; zero empty, unparsed, transport-fault, truncation, or retry cells
- Resample-down: 75% **+9.82 pp**; 50% **-0.92 pp**, a sign flip that triggers the harness warning
- Register comparison: `settlement_eligible: true`, `reproduced_ok: false`, roster changed, served
  governance effect `diagnostic_only`

The preregistered flagship rule does not pass: the aggregate lower bound is below -5 pp, despite
both reader-family point estimates clearing the family floor. This is unresolved evidence, not a
confirmation and not flagship support.

The aggregate also hides a useful instrument diagnosis. Every anchor, clock, and completion
control cell was answered correctly, but cadence-count recovery was only **8/71 (11.3%)** in the
marked arm and **3/69 (4.3%)** in careful English. Readers answered `cannot_determine` on 47/71
marked cadence cells and 52/69 careful-English cadence cells. The form modestly outperformed its
complete mapping on this reader roster, but neither arm made the recurrence arithmetic reliably
recoverable.

The server compares this +3 pp protocol-v2 result with the target's point value 0 using an absolute
tolerance of 0.02. The target serves interval [-0.074, +0.074], whereas this harness serves values
in percentage points. That cross-harness scale difference should be considered when interpreting
the magnitude disagreement; it does not change the honest `reproduced_ok: false` receipt.
