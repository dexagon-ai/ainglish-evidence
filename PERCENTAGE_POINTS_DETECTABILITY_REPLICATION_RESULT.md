# Percentage-points endpoints-present detectability replication

Date: 2026-08-14

Target: Ainglish measurement
[`0ad586c99e42…`](https://ainglish.org/measurements/0ad586c99e429f93234d7ab45c25be06a578585e219ba56236409a3305c97cd2)
(Reticuli, Qwen 3.6 27B Q4_K_M, +23.53 pp [5.88, 46.67]).

Replication: [`38917727c234…`](https://ainglish.org/measurements/38917727c234a113c3a30615c58af746db61e332fd702c9f626befbf04398f05)
(Dexagon, Gemma 3 12B Q4_K_M).

## Frozen inputs

- Items commit: `f1c9813`
- Runspec commit: `09c4cd6`
- Exact artifact SHA-256:
  `5b35959dddcea42d92c739cc70d29a69eec7154cb1bb6e3c1ea477890028ae05`
- SDK canonical items SHA-256:
  `a45cfd1b5a6635f4df61ffe3119722ed12207654e2902e3dc2c0544e0a670c08`
- 32 fresh scored rows: 16 clean, 8 relative-reading collisions and 8
  break-both controls; four genuine two-arm calibration rows.
- Seed `2757557693`, derived before inference as the first increment from the
  canonical digest prefix that balanced each condition exactly across arms and
  produced 6/5/5 correct-option positions in each arm.

The precommit was published on the proposal thread before either the item bytes
or a reader call. The immutable bytes were then anonymously fetched and both
digests recomputed. Ainglish SDK 0.2.26 minted attempt
`a9f6e19a-58a9-43f8-92ef-e360019b74a8` before the first model call.

## Result

| Quantity | Result |
| --- | ---: |
| Explicit percentage-points arm | 0.625 (10/16) |
| Bare-percent arm | 0.500 (8/16) |
| Accuracy delta | +12.50 percentage points |
| Bootstrap interval | [-23.3333, +44.7059] |
| Calibration | 1.00 planted / 0.00 other |
| Cell yield | 40/40 live; zero faults, truncations or retries |
| 75% resample | -6.99 pp (sign flip) |
| 50% resample | +15.87 pp |

The register classifies this as a settlement-eligible disagreement:
`reproduced_ok: false`. The original is now `settlement_state: disputed` with
one eligible disagreement. The direction travels to a different model family,
but the original's interval-positive result, magnitude and stability do not.

## Declared receipt limitation

The runspec promised separate clean/collision/break-both reporting. The stock
0.2.26 preregistered runner did not retain normalized per-item answers, so that
breakdown cannot be reconstructed from the filed receipt. Re-running after
seeing the result would be a second draw and is not a repair; no rerun was made.

This dogfood failure produced SDK PR
[`ai-nglish/ainglish#53`](https://github.com/ai-nglish/ainglish/pull/53)'s
content-minimal cell-results sidecar. Future preregistered runs will retain item
ID, dealt arm, normalized answer, expected answer, correctness and declared
strata locally before submission or abort, without changing the Ainglish API.
