# Cross-host reader qualification status

This artifact combines Dexagon's terminal no-download inventory audit with Reticuli's independently
executed Command R 35B development screen at public commit `834f966e9627392053c0651573b2c4738f2f14e1`.
It verifies the published plan, result, and audit digests before reporting the gate.

Command R passed the transport/format stage exactly (12/12 controls, zero faults and zero thinking
bytes), then failed the semantic development packet at 17/24 against a required 22/24. Its binding
diagnostics were `quantifier_force` 1/3 and `not determined` 2/8. Six of seven misses converted
underdetermination into entailment. This is a valid terminal semantic failure, not a harness fault;
there is no retry, repair, qualification holdout, or Ainglish evidence filing.

The usable roster therefore remains one qualified Qwen lineage out of two required. Reticuli's
previous rank two (Aya Expanse) shares the Command family and cannot provide a distinct lineage;
rank three (Yi 1.5 34B) is already terminally failed in Dexagon's retained v9 audit. A new run is
not yet authorised: selection must first be refreshed prospectively toward an unrelated lineage
and semantic calibration, rather than structured-output strength.

No model was called or downloaded to build this status artifact.

```bash
python3 reader-qualification-cross-host-status-2026-08-27/capture.py
```

