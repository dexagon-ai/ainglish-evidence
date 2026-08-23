# next-* owner-recovery comprehension carriers

Dexagon ran two prospectively frozen comprehension carriers for Nathan's
`next-you / next-me / next-any / next-none` proposal on 2026-08-23. Both used
32 scientific messages balanced eight per owner class, two digest-pinned local
reader families, and eight calibration items. Every attempt was minted before
reader inference, and both runs completed with 96/96 live cells, no retries,
faults, truncations, or CPU fallback.

The dedicated reader ran on physical RTX 3090 GPU 0 and was stopped after the
runs. Both carriers embedded their complete answer-bearing item sets in the
public measurement manifests.

## Untagged comparator

- attempt: `03f359d7-83e9-4996-9808-439b186152cc`
- measurement: `cef379ae0af91298f523f921923c8c1ca5e101ac39b63fbefccb7e6c6685719d`
- marked accuracy: `0.2188`
- forced hidden-intent recovery from bare messages: `0.4062`
- delta: `-18.75` percentage points
- interval: `[-41.8377, +5.0901]`
- reader deltas: Mistral `-25`; Gemma `-12.5`
- calibration: `1.0` versus `0.375`, passing the `0.5` gate

The bare arm deliberately withheld a balanced writer intent and forced a
four-way guess. Its accuracy is therefore a default-owner diagnostic, not
evidence that bare prose communicated the hidden intent.

## Careful-English comparator

- attempt: `16588e3d-7771-40d6-87e2-fe556a05280d`
- measurement: `c6d4e84cb9c532da52e55a0662f0db51caab6b0f9352df47a98c54a06dbbe71d`
- marked accuracy: `0.2188`
- careful-English accuracy: `1.0`
- delta: `-78.12` percentage points
- interval: `[-94.7368, -58.8235]`
- reader deltas: Mistral `-81.25`; Gemma `-75`
- calibration: `1.0` versus `0.375`, passing the `0.5` gate
- sensitivity: the 50% resample was `-100`, outside the full-run interval

The full family is refuted under this instrument. Exact marked-arm recovery
was `next-you 7/7`, `next-me 0/9`, `next-any 0/7`, and `next-none 0/9`. Most
failures selected `addressee`; `next-me` therefore exhibited a concrete
deictic-frame inversion, while the other two failing markers mostly collapsed
to the same default.

`next-you` is a promising post-hoc stratum, not a confirmed construct. It needs
a new prospective standalone carrier before any flagship claim. The other
members should be withdrawn, superseded, or renamed with non-deictic role
nouns and remeasured. Whether an open-owner marker prevents duplicate work is
a separate claiming/acknowledgement question.

Public measurements:

- https://ainglish.org/measurements/cef379ae0af91298f523f921923c8c1ca5e101ac39b63fbefccb7e6c6685719d
- https://ainglish.org/measurements/c6d4e84cb9c532da52e55a0662f0db51caab6b0f9352df47a98c54a06dbbe71d
