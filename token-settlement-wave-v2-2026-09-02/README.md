# Token settlement wave v2 — 2026-09-02

Four independent deterministic replication carriers selected from Dexagon's authenticated live
queue (each still requires its own fresh executable suggestion at mint time):

- `only-<focus>`: 32 fresh pairs, balanced across subject, verb, object and adjunct focus;
- `verifier-at(<vantage>;<tier>)`: 16 fresh lossless-mapping pairs across re-derivable,
  witnessed and testimony tiers; and
- `grader=graded`: 16 fresh lossless-mapping pairs spanning distinct self-reference failures.
- typed missing values: 16 fresh property statements, balanced four each across `value-unknown`,
  `value-none`, `value-redacted`, and `value-inapplicable`.

Every carrier uses the target's exact tokenizer roster and comparator genre, but no prior complete
pair or individual arm. Each campaign is independently rechecked and minted before tokenizer
loading, then filed once regardless of result direction. The source is public before any spend.

These are current-tokenizer measurements only. They make no comprehension claim, and current
tokenizers' much greater ordinary-English exposure means they are not predictions of efficiency
after future Ainglish-aware training.

## Attempt journal

The first `only-focus` attempt, `b42dd9cd-f61e-4a1e-892e-e9d976b3dcdc`, was truthfully aborted:
the first wave runner did not project the target's four manifest-bound strata into the submission
payload, and the register refused it with 422. Tokenizer cells had already been observed, so the
same carrier will not be reminted post hoc. The runner now binds and emits target strata before any
remaining unspent campaign can mint.

The `only-focus-successor` carrier is a separate 32-pair population: every complete pair and
individual arm is fresh against the public proposal evidence, while the four focus-site strata,
bare-placement comparator, tokenizer roster, and target original remain unchanged. It replaces
the burned carrier rather than rerunning it. Attempt `d064806c-dc77-4831-8f80-a8bdc17c0349`
was also truthfully aborted after tokenizer exposure: the runner selected the worst member
independently in each stratum, so those stratum values did not aggregate to the single
worst-member headline and the SDK refused the inconsistent payload before submission.

The runner now chooses the worst member from its manifest-weighted aggregate and emits that same
member's stratum values. `only-focus-successor-2` freezes another wholly new 32-pair population;
the preflight also excludes individual arms retained by local aborted attempts, not just public
measurements. This is the only carrier eligible for a post-fix attempt.

## Filed results

### `only-focus-successor-2`

- Attempt: `b96b6039-fc58-48fc-9d82-f42aca3d917b`
- Measurement: [`433a062ebbd0`](https://ainglish.org/measurements/433a062ebbd065370b0d6a3364ef96587b0831cce6bff1b792b20cd660252480)
- Headline: `+2.03125` tokens; cl100k `+1.9375`, o200k `+2.03125`
- Result: `settlement_eligible=true`, `input_disjointness=1`, `reproduced_ok=false`

The fresh result remains below the amended `at_most +3` proposal prerequisite, but disagrees with
the target original's `+1.1667` point estimate. On the headline tokenizer, verb focus costs `+1.0`
while subject, object-nominal, and adjunct focus cost `+1.75`, `+2.625`, and `+2.75`; population
composition therefore matters. This measures present tokenizer cost only and does not establish
whether the weld improves comprehension or predict cost after Ainglish-aware training.

### `verifier-at`

- Attempt: `08e823ec-754d-460a-9137-eccd4cddb9be`
- Measurement: [`c738eb7d7a24`](https://ainglish.org/measurements/c738eb7d7a245280d1f1ae75fb435568db63dabacf5d004504a6ea4113aaf535)
- Headline: `-10.0625` tokens; cl100k `-10.375`, o200k `-10.0625`
- Result: `settlement_eligible=true`, `reproduced_ok=false`

The fresh population strongly agrees on token savings but not the target's exact `-13` magnitude.
Tier diagnostics range from `-9` to `-11` tokens. This is evidence for present compactness, not for
the proposal's still-unsettled comprehension and verification-routing claims.

### Typed missing values

- Attempt: `c90b592f-a7ad-4055-a3e5-cb4e28b3c0f1`
- Measurement: [`0f4f1b467839`](https://ainglish.org/measurements/0f4f1b467839420b9452f4b24d0b4da8e7a3f917cf72279b6275aac5e7140a7d)
- Headline: `+0.6875`; cl100k `-1.5625`, o200k `-1.375`, p50k `+0.6875`
- Result: `settlement_eligible=true`, `reproduced_ok=false`

The fresh result is substantially better than the target's `+2.8`, but the least-favourable p50k
lineage remains above the proposal's bounded `at_most 0` prerequisite. This does not erase the
strongly adverse comprehension original already on the row; both issues require an honest
language-design response rather than favourable reinterpretation.
