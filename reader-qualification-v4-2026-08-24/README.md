# Reader qualification v4

This package seeks one additional construct-blind reader lineage to combine
with the Gemma 3 edition that individually passed the untouched v2 holdout.
The candidate is a previously untested Qwen 3.5 9B Q4_K_M edition. It is not a
retest of the 27B edition whose v2 development run exhausted a 16-token bound.

Development deliberately reuses the already-exposed v3 development controls;
they are not qualification evidence. If the new edition passes development,
a new ordinary-English holdout disjoint from every burned control is authored,
committed, and pushed before its one allowed run. The holdout must have every
output parseable, at least 34/36 correct overall, and at least 5/6 on each of
six axes. Failure is published and stops the conditional `some-or-all`
measurement; success permits a scientific roster with the v2-qualified Gemma.

The initial development run emitted 19 exact codes and all 19 were correct;
five harder items exhausted a 1024-token hidden-reasoning bound before emitting
any visible code. The one allowed construct-blind revision therefore changes
only the transport to Ollama native chat with `think=false` and restores a
16-token answer bound. The tuned development set is deliberately unchanged.

## Outcome

The tuned development check passed at 22/24 with 24/24 exact codes and every
axis above its development floor. The new holdout was then frozen and pushed
before its only run.

The holdout did **not** qualify the reader. It emitted 36/36 exact codes and
scored 33/36, with axis scores `6/6 quantifier`, `5/6 set membership`, `6/6
negation`, `6/6 disjunction`, `5/6 conditional`, and `5/6 reference`. The
registered gate required 34/36 overall and at least 5/6 on each axis.

The misses were not transport failures and are not re-keyed: the reader declined
the membership inference in “only red-team members may approve; the reader
approved”, affirmed the consequent from “if the scan succeeds, publish; it was
published”, and resolved an intentionally ambiguous pronoun. All three original
keys remain defensible. `roster_ready` is therefore false, the qualified Gemma
reader still lacks a second qualified lineage, and no `some-or-all`
comprehension attempt was minted or scientific item exposed.
