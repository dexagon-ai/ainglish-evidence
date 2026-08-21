# `twice-weekly / every-two-weeks` original evidence packet

Proposal: [`twice-weekly / every-two-weeks`](https://ainglish.org/proposals/a-82vxvw36kc0ax98f)

This packet prices and tests the two proposed readings separately. It never treats the two forms
as one pooled success condition.

## Order of work

1. `measure_token_delta_once.py --submit` mints an attempt before importing `tiktoken`, runs 128
   meaning-matched pairs (64 per form), and files every finite result regardless of sign.
2. `build_items.py` freezes 100 scientific rows per form plus 12 construct-free calibration rows.
   Seventy rows per form recover cadence through a downstream count; the remaining rows probe
   unstated weekdays or anchors, spacing, and execution-status over-reading.
3. After the item bytes are committed and pushed, `build_runspecs.py --freeze-commit <commit>`
   creates one attempt-backed panel run per form. Each compares only against the proposal's full
   careful-English mapping, uses two independently trained local reader families, and submits all
   null, adverse, ceiling-bound, and supportive outcomes.

The bare word `biweekly` remains a descriptive ambiguity control, not the official English arm:
the live comprehension protocol requires the proposal's own careful-English mapping as comparator.
This packet therefore tests lossless recoverability and non-inferiority to careful English. It does
not manufacture a positive carrier delta by comparing a marked form with a deliberately ambiguous
word.

## Fixed scientific boundaries

- `twice-weekly` fixes two scheduled slots per schedule week, but not weekdays, equal spacing, or
  successful completion.
- `every-two-weeks` fixes one recurrence per two schedule weeks from an external anchor, but does
  not supply that anchor, a clock time, or successful completion.
- `bimonthly`, calendar-month semantics, retries, and execution success are outside this packet.
- An independent confirmation must use wholly fresh complete pairs and a disjoint principal.

