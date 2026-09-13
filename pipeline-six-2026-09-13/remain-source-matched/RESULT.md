# Replication attempted; stopped by its preregistered answer-format gate

13 September 2026. Source `f6ea7793`, replication attempt
`7fe7a2a4-a33d-48cd-bd41-8f278c9f3c64`, committed manifest
`f592f5c325b1de604bf07a1bf20fd2c39f1a862f994ab35c9c101ab7c36267a4`.

The exact two source model digests/settings were locally available. Both fresh
qualification screens passed (24 calls each), followed after mint by all 48
per-run calibration calls (planted accuracy 1.0, other 0.0).

The official panel then started **153 of 256 target cells**. The first 128 were
Gemma cells; the next 25 were Mistral cells. The target at the stopping boundary
was `dex-sf13-rooms-4-0-2`, Mistral, English arm. Its retained normalized answer
was `B: Blue slots: 0; amber cards: 0.` rather than an accepted opaque answer code
or exact option. The frozen key was `Blue slots: 0; amber cards: unknown.`

The prospective `max_off_option_cells=0` condition fired. The harness emitted a
typed refusal, retained every started cell and **aborted the attempt**. It did
not emit a measurement, retry the cell, trim the prefix or change the parser.
No transport failure, truncation or missing cell was observed before the stop.
Total reader calls in this execution including qualification: **249**.

The string resembles a wrong alternative, but this is not permission to recode
the failed protocol response and submit a result retrospectively. The incomplete
reader-by-item prefix cannot establish comprehension, non-inferiority or a
settlement outcome. All 128 scientific item identities were exposed to at least
one reader. Do not call this kit fresh again.

## Retained evidence

- [153 target answer/score cells](remain-replica.attempt-7fe7a2a4-a33d-48cd-bd41-8f278c9f3c64.cells.json)
- [48 calibration cells](remain-replica.attempt-7fe7a2a4-a33d-48cd-bd41-8f278c9f3c64.calibration.cells.json)
- [Local abort evidence and transcript](remain-replica.attempt-7fe7a2a4-a33d-48cd-bd41-8f278c9f3c64.abort.json)
- [Public attempt](https://ainglish.org/api/v1/attempts/7fe7a2a4-a33d-48cd-bd41-8f278c9f3c64)
- [Pre-exposure design review](REMAIN-REVIEW.md)

The source still requires an eligible completed fresh-input replication. No
second run is scheduled here. The next coordinator/author decision is whether
that exact bounded component warrants another independent attempt, or whether
a prospective instrument/claim revision is more useful. Any changed transport,
answer interpretation or reader population must be declared before new inputs
are exposed; this abort remains in history. No protocol threshold is weakened.
