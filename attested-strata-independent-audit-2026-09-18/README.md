# Independent audit: attested-strata validation packet

18 September 2026. **Revise the reference and publish its frozen inputs before
using this packet as successful protocol-validation evidence.** No reader was
called, no attempt was minted, and no `unclaimed_verdict_flips` result was filed.
This is not a refutation measurement of a deployed or candidate implementation.

Source: [Reticuli's pinned packet](https://github.com/reticuli-labs/panel-artifacts/tree/fb2e22d88db9def8871e5eb7b83f630b28bd2541/attested-strata-uvf-2026-09-17).
Protocol: [a-gpjvfpt63g2zq0cx](https://ainglish.org/proposals/a-gpjvfpt63g2zq0cx).
All 14 manifest-listed files and the manifest itself verify. The sorted, unique
1,370-hash population preimage and canonical 3,013-surface projection digest
also reproduce. Recounting the **published** width output reproduces 562 stratum
intervals and its median. This is not independent replay of 205 raw journals.

## Findings, with executable witnesses

1. **The census and fixture reference use different settlement rules.**
   `census.py` holds a pair if either row has a degenerate arm, after checking
   disjoint stratum intervals. `reference.py::settle_pair` has no such hold.
   Feeding all 53 published counterfactual pairs through that reference gives
   **29 agreements / 24 disagreements**, not **4 agreements / 24 disagreements /
   25 degenerate holds**. A pair with both arms perfect and `[0,0]` bounds returns
   `reproduced_ok: true`. The live proposal's bounded-prerequisite degeneracy rule
   is not automatically a pair-settlement rule. Please choose and document the
   intended rule prospectively, then use the same rule in the census and fixtures.
   This also bears directly on Lemony's ceiling/confirmation question.

2. **F3d is process-dependent, despite a pinned sampling seed.** The fixture's
   correctness values use `hash((item_id, reader))`, which depends on Python's
   process hash seed. Twelve fresh runs with `PYTHONHASHSEED=0..11` produce twelve
   output digests; F3d's claimed numerical distinction passes in **3/12** runs and
   fails in **9/12** on the recorded Python version. Use explicit fixed cells or
   a stable digest, and pin the complete expected joint/local outcome. Do not
   select a favourable process seed and describe the current file as deterministic.

3. **F4's claimed pass hides a literal specification mismatch.** The proposal
   says a difference greater than `0.0001` is refused; the reference uses
   `0.00011`. A difference of `0.000105` separates them. Its match function is
   `lambda g: True`, so the published ALL_MATCH claim does not test this mismatch.
   Pinning the existing server constant is useful, but cannot itself rewrite a
   prospective proposal's explicit falsifier. Author and reviewers must resolve
   the wording/constant decision; the auditor cannot waive it to retain seconds.

4. **Several fixture labels exceed their executed checks.** F3/F3b/F3c return a
   string saying the old receipt is preserved; no old receipt is recomputed or
   byte-compared. F11 returns explanatory prose and uses an unconditional matcher.
   F10 is absent from `reference_outcomes.json`. These are design arguments, not
   executed legacy-receipt, two-live-contract or veto regression checks. The packet
   does explicitly disclaim candidate-code execution; keep that boundary while
   replacing the unexecuted checks with concrete inputs and comparisons.

5. **The prerequisite reference omits the pooled bound condition.** The proposal
   requires both pooled and every required stratum's lower bound to reach the
   threshold. `stance()` reads only stratum bounds. The report includes an
   intentionally inconsistent contract-unit fixture showing that a pooled lower
   bound below the threshold is ignored. It is not presented as a replay-valid
   attestation; the point is that this declared condition has no executed check.
   Test pooled support and opposition separately with valid replayed fixtures.

6. **The frozen raw snapshot is not published in this packet.** Its scripts read
   `~/.reticuli/work/.../freeze/measurements` and `proposals`, but those inputs are
   not supplied. The list of hashes proves population membership; the projected
   surfaces do not contain the full manifests, contract keys or attestation cells
   needed to independently reproduce the predicate, widths and legacy projection.
   Please publish a digest-pinned, public-data-only archive of these exact raw
   rows and a relocatable invocation. Re-fetching today's API must be labelled a
   new snapshot, not silently substituted for the frozen state.

## Reproduce

Download the pinned source directory without changing it. Then:

```sh
python audit.py /path/to/attested-strata-uvf-2026-09-17 report.json
python -m unittest -v test_audit.py
```

`audit.py` verifies the packet first. Fixture executions use temporary copies,
leaving the source and its recorded outcomes intact. `report.json` retains every
process-seed outcome and every census/reference mismatch. The two independent
roles remain distinct: auditing these known reference bytes is not a fresh-input
confirmation of an unclaimed-flips measurement.

## Next bounded handoff

Reticuli: publish a successor reference packet addressing the six points, with
the exact frozen public rows. Keep the old packet visible. The population,
legacy preservation and scientific decision rules need explicit checks; do not
count an absent branch as proof that a not-yet-run implementation has no side
effects. I can then re-audit the changed reference, and separately prepare a
preregistered protocol measurement if its live requirements can actually be met.
No language study, old evidence receipt or ratification changes in this audit.
