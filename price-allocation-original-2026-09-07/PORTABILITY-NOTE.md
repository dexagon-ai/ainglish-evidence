# Preregistration preparation correction, before target exposure

The first dry/live-preparation path in commit937aa6e stopped locally before any
preregistration or target call: the SDK rejects manifest float0.95 as non-portable
under the register's canonical-number contract. No failed qualification or target
answer motivated this change. Both completed neutral screens remain unchanged.

The per-attempt recovered-headroom threshold is now the exact integer1. With
eight fully yielded calibration cells in each arm, this admits exactly the same
integer count pairs as0.95: when detectable_correct<8, recovered headroom is at
most7/8; when detectable_correct=8 and other_correct<8 it is1. The independent
minimum absolute gap remains0.5 and the zero-fault rules remain unchanged.

No question, gold key, reader, result-selection rule or scientific target changes.
The old source bytes remain in937aa6e; the corrected runner is re-pinned and
published before preparation/mint. This note is not an inference result.
