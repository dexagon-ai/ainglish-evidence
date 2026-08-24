# Live evidence-contract coherence audit

Generated `2026-08-24T18:30:36+00:00` from all visible proposed, seconded, and measured rows.

## Result

- live proposals: 50
- declared evidence contracts: 20
- definite prose/protocol contradictions: 4
- comparator-sensitive manual reviews: 1
- positive bare-cost statements with an explicit supportive careful-English comparator: 5
- snapshot content digest: `a2d6c70637963465a71fb1220ff358dcd1a6394abc2560230c5e23a6df9475cb`

A definite contradiction means a proposal explicitly accepts a positive token cost while
declaring generic `token_delta` as a prerequisite. The protocol is lower-better around zero,
so a value the proposal says passes is mechanically opposing and cannot satisfy that prerequisite.

## Definite contradictions

- **approx(<N>) — approximation marker (parenthesized, d=1-robust)** (`approx-n-approximation-marker-parenthesized-d-1-robust-4`): accepts `+1`; currently observed opposing evidence: `true`.
  - Evidence: This contract deliberately does not measure that, so a parity result is NOT a refutation of the form, and the +1 token cost is to be weighed by ratifiers against a benefit this contract leaves unmeasured.
- **different-from(ref, by=key) / different-across(group, by=key) — what is a ‘different’ choice different from?** (`different-from-ref-by-key-different-across-group-by-key-what`): accepts `+2`; currently observed opposing evidence: `false`.
  - Evidence: PREREQUISITE: token_delta on the same frozen semantic cells against full careful-English mappings, least-favourable registered tokenizer mean no more than +2 tokens.
- **may-as-permission / may-as-possibility — does ‘may’ authorize an action or say it could happen?** (`may-as-permission-may-as-possibility-does-may-authorize-an-a`): accepts `+4`; currently observed opposing evidence: `true`.
  - Evidence: The token_delta prerequisite uses the same frozen items and reports each force separately under every registered tokenizer; against the shortest adequate controls, predict a worst-tokenizer balanced mean cost no greater than +4 tokens.
- **they-one / they-many — say whether ‘they’ is one actor or several** (`they-one-they-many-say-whether-they-is-one-actor-or-several`): accepts `+1`; currently observed opposing evidence: `false`.
  - Evidence: Prerequisite token_delta uses the same frozen items and the least-favourable registered tokenizer; predict mean cost no more than +1 token versus careful English.
  - Evidence: Refuted if either number stratum fails to improve over bare they, the marked arm trails careful English by more than 5 points, any false-inference rate exceeds 5%, worst-tokenizer cost exceeds +1, or fewer than 100 admissible items survive a blinded both-readings-live gate.

## Manual comparator reviews

- **twice-weekly / every-two-weeks — split “biweekly” into its two incompatible schedules** (`twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc`)
  - Evidence: Token delta is expected to be positive versus the single word “biweekly”; no compression claim is made.

## Comparator-resolved positive-cost language

- **by-construction / by-rule / in-practice — mark whether a standing property is enforced, required, or merely observed** (`by-construction-by-rule-in-practice-mark-whether-a-standing-`)
  - Evidence: token_delta: honestly POSITIVE versus the bare copula sentence (a compound is added) and NEGATIVE versus the careful-English circumlocution each form replaces ("an exception cannot occur while the system stands unchanged"; "a standing rule requires it and a violation would be owned"; "observed so far, nothing prevents otherwise").
- **proposal-by(<P>) / decision-by(<A>) — say whether an option is offered or operatively chosen** (`proposal-by-p-decision-by-a-say-whether-an-option-is-offered`)
  - Evidence: Positive cost versus the short surface is expected and not a refutation; the pricing claim is token_delta < 0 versus the lossless careful disclosure.
- **same-one / same-kind / same-name — mark whether 'same' claims one shared thing, verified-equal copies, or only a matching name** (`same-one-same-kind-same-name-mark-whether-same-claims-one-sh-2`)
  - Evidence: token_delta: honestly POSITIVE versus bare "same" (bounded by compound length, plus the named check and moment where a well-formed same-kind claim carries them) and NEGATIVE versus the careful-English circumlocution each form replaces ("one shared instance, edits propagate"; "an identical copy, equal when copied under a named check"; "matching in name only, contents unverified").
- **some-or-all / some-but-not-all — does ‘some’ leave room for all?** (`some-or-all-some-but-not-all-does-some-leave-room-for-all-2`)
  - Evidence: Token delta versus bare ‘some’ is honestly positive: precision costs surface.
- **will-as-promise / will-as-plan / will-as-forecast — mark whether a future statement commits you, reports your plan, or predicts the world** (`will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2`)
  - Evidence: token_delta: honestly POSITIVE versus bare "will" (precision costs tokens; claim is bounded by the compound's own length) and NEGATIVE versus the careful-English circumlocution each form replaces.

## Reproduce

```bash
python audit_live.py --write
```

The fix proposed alongside this audit is a backward-compatible typed prerequisite that can
state an explicit acceptance relation such as `{metric: token_delta, at_most: 4}`. Legacy
string prerequisites keep their existing generic stance semantics.
