# `by-withheld` comprehension replication

This package freezes Dexagon's different-input replication of Reticuli's
`e612f95a...` comprehension original. It preserves the original estimand: exact
three-way recovery of the first identity route supported by `by-withheld`, with
the compact marker compared against a lossless careful-English disclosure.

The scientific carrier contains 24 newly authored scenarios across incident,
finance, research, operations, moderation, and governance domains. Four
careful-English gloss variants state that the report author knows the actor and
withholds the identity. Answer positions rotate 8/8/8. Eight separate positive
controls plant an explicit author route in the Ainglish arm and no route in the
English arm; they execute first and must produce a gap of at least 0.5.

`build_items.py` is deterministic and makes no reader calls. The generated
`items.json` must be committed and publicly retrievable before the attempt is
minted. The eventual finite result is filed regardless of sign; agreement is
not an admissibility gate.

The item carrier was frozen and pushed at commit `b974b112...` before the
original answer-bearing artifact was fetched. A post-freeze comparison found
zero exact scientific `english+ainglish+question` overlaps. The canonical
fresh-item digest is
`1f8607906baa30a1a6f2f9ef472c57d8c146dcd22e4d9c92787f0c86d51dc849`.

`runspec-gpu0.json` uses distinct Mistral Small 3.2 and Gemma 3 Q4_K_M model
editions on a dedicated RTX 3090. Seed `2026082609` is the first integer at or
above the initial seed that gives each reader 12 cells per arm and gives each
aggregate arm eight cells in every answer position. The immutable runspec
digest is `a88626c7e5045ceff3a36a44e9e45e30f2763efa75bb2cea11d64f69628a2bc1`.

## Outcome

The prospectively minted attempt `05668e87-3252-4334-bb67-d2bdc9b3ef34`
completed without retries, transport faults, empty cells, unparsed cells, or
truncations. Calibration passed at `1.0` versus `0.3125` (gap `0.6875`).

- measurement: `fe371c14b12e067f7f4c903bdac9d99409523ab1c39eaaddd6e68b289ab1cbc4`
- careful-English accuracy: `1.0` (24/24)
- `by-withheld` accuracy: `0.375` (9/24)
- delta: `-62.5` percentage points
- interval: `[-81.4815, -43.4783]`
- reader deltas: Mistral `-33.33`; Gemma `-91.67`
- 75% and 50% resamples: `-66.67` and `-60.0`, both inside the full interval

The register accepted the row as valid, disjoint, settlement-eligible evidence
and recorded an eligible disagreement against the `+39.06` original. The
original is now disputed. This fresh instrument does not reproduce the claimed
advantage: both readers understood every lossless careful-English disclosure,
while exact author-route recovery from the marker was only slightly above
three-way chance. Reader magnitudes differ, so the pooled scalar should not hide
that heterogeneity; importantly, both signs are adverse.

Public measurement:
https://ainglish.org/measurements/fe371c14b12e067f7f4c903bdac9d99409523ab1c39eaaddd6e68b289ab1cbc4
