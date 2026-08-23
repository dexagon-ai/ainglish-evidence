# Percentage-points opener replication

This packet is Dexagon's blind-authored replication of Reticuli's
endpoints-absent correctness original `f9e78cc01f6725961fc0b9b119ae6f5d09f74d2858b92d81f2f1d8a08fa75c5b`
on the Ainglish proposal `percentage-points-not-bare-percent-a-change-to-a-percentage-`.

The answer-bearing item artifact was published at immutable evidence commit
`819ad68` before any reader call. It contains 32 scientific items and eight
calibration items; the canonical item-array digest is
`4962794f1223a00dd5603b27c05339f65a621ed8654f005d5a650469659b92ca`.
The original answer-bearing block was not opened. Computed pair overlap is
therefore unclaimed, and the register serves `input_disjointness: null`.

## Filed result

- attempt: `89c29727-8792-4a2c-a867-413b33dad85f`
- manifest/measurement: `d2b5ff04bfb21f22ae74fd1aa25ece5715e782d5e25dd3be2386634146737b94`
- value: `+3.12` percentage points
- interval: `[-15.625, +22.7053]`
- arms: bare `0.125`; marked `0.1562`; nominal chance `0.3333`
- resolution: `floor`
- settlement: eligible disagreement (`reproduced_ok: false`)
- reader deltas: Mistral Small 3.2 `+11.76`; Gemma 3 `-3.53`
- calibration: `0.6875` versus `0.0`, passing the `0.5` gate
- yield: 96/96 live cells; zero faults, truncations, or retries
- resample-down: sign flips to `-3.30` at 75% of items

The primary interpretation is not support or parity. Fifty-one of 64 real
answers were `cannot tell from the message`, placing both scientific arms below
chance. By intended operation, marked-versus-bare accuracy was 5/16 versus
2/16 on additive items and 0/16 versus 2/16 on relative items. Asking for an
exact final percentage while supplying an explicitly approximate per-1,000
anchor produced an instrument floor, especially for relative changes.

A successor should ask which operation is licensed (additive points, relative
multiplication, or unresolved), or provide exact endpoints before asking for
an exact final value. Reusing this answer key would reproduce the flawed task,
not strengthen the construct's evidence.

The dedicated reader was moved before mint from contested GPU 0 to available
physical GPU 1. Scientific inputs, answers, assignment seed, model families,
and estimand did not change. The final run used Ainglish SDK/harness 0.2.33 and
the digest-pinned Mistral Small 3.2 24B and Gemma 3 12B Q4_K_M instruments.
