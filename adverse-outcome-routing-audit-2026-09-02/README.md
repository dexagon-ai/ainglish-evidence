# Adverse and null outcome routing audit — 2026-09-02

This audit asks whether active proposals with non-performant evidence are being left indefinitely
in a positive progression lane. It distinguishes an adverse result on the proposal's declared
claim carrier from an adverse or neutral result on a prerequisite axis that cannot establish the
full claim.

## Live finding

Across the 81 active `seconded` and `measured` proposals inspected on 2026-09-02, no proposal had
confirmed adverse evidence on its declared claim-carrying metric. The register therefore had no
scientifically justified candidate for forced rejection on that basis.

Five proposals did have confirmed non-supportive token-cost observations while still lacking the
comprehension evidence that carries their principal claim:

| Construct | Current token observation | Missing claim-carrier work | Correct route now |
|---|---:|---|---|
| `among-others` / `and-no-others` | +2.5, adverse | original comprehension | measure comprehension; report token cost prominently |
| `approx(N)` | +1.1, adverse as a pure saving | original comprehension | measure comprehension; assess against its bounded-cost wording |
| `may-as-permission` / `may-as-possibility` | +2.5, adverse | original comprehension | measure comprehension; report token cost prominently |
| `moved-earlier` / `moved-later` | +1.5, adverse | comprehension and tag fidelity | complete both declared axes before a claim verdict |
| `this-once` / `from-now-on` | +1, neutral/adverse cost | original comprehension | measure comprehension; do not call it token-efficient now |

Rejecting these proposals solely from token cost would overstate what was tested. Conversely, the
present English-training and tokenizer advantage does not make the observed cost disappear. The
truthful public statement is that these forms are presently costlier for the named tokenizers and
may still produce a comprehension benefit; both parts require evidence.

## Existing terminal routes

The register already distinguishes several reasons work can stop: confirmed adverse evidence can
produce `rejected`; a failed ballot produces `vote_failed`; authors can use `withdrawn`; custodial
replacement produces `superseded`; attention expiry produces `lapsed`; and post-ratification
reversal can produce `deprecated`. These should remain separate because they answer different
questions about the proposal.

A proposed reversible `shelved` state would be useful for sound but currently non-actionable work,
especially when the necessary model, author, or instrument is unavailable. That protocol proposal
is itself only `seconded` and awaits independent protocol evidence for its declared claim. It must
not be treated as deployed policy before completing that review path.

## Operational rule

When confirmed adverse claim-carrier evidence appears, preserve the measurement, show its target
and settlement status, and let the normal verdict recalculation move the proposal to the appropriate
negative state. Do not delete an inconvenient result or replace it with an editorial label. When
only a prerequisite is adverse, display the limitation and finish the other declared axes before
making the full-claim decision.
