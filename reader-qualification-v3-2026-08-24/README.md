# Reader qualification v3: additional-lineage tournament

This construct-blind tournament seeks at least one new reader lineage to combine with the Gemma 3
edition that individually passed the untouched v2 holdout. It does not retest the Mistral edition
that failed v2 and does not treat repeated screens as independent chances to qualify it.

The candidates are a new generic-literal Qwen 2.5 edition and the previously unused Qwen 3.8
screening edition. Development uses only ordinary English. After those results, all passing
candidates are frozen into a new, disjoint holdout before any holdout call. Neither stage is
proposal evidence.

No scientific comprehension attempt may be minted unless at least one new Qwen edition passes the
untouched v3 holdout with every output parseable, at least 34/36 correct overall, and at least 5/6
on every axis. A later scientific roster must include the independently qualified Gemma edition so
that it spans at least two vendor/model lineages.

## Development round one

Neither initial edition passed. Qwen 3.8 returned 24 bound-exhaustion truncations before a visible
code at `max_tokens=16`. Qwen 2.5 emitted 24 exact codes but scored 20/24, below the registered
22/24 floor, with 2/4 on disjunction. These are development results, so one construct-blind
configuration revision is allowed before the holdout exists: Qwen 3.8 receives a 1024-token output
bound, while Qwen 2.5 receives an entailment-focused system instruction derived from the exposed
errors. The exact same development items are deliberately reused for that development check. The
later holdout may not reuse any of them.

## Holdout outcome

The Qwen 3.8 edition did not qualify. On 36 untouched items it emitted 34 exact codes and scored
31/36, with axis scores `6/6 quantifier`, `4/6 set membership`, `6/6 negation`, `5/6
disjunction`, `5/6 conditional`, and `5/6 reference`. The frozen gate required 36/36 exact codes,
34/36 correct, and at least 5/6 on every axis.

One disjunction key is deliberately conservative: bare “north or south” without an exclusivity
rule was scored `cannot tell` for whether both may be used, while the reader chose `yes`. Counting
that item for the reader would produce 32/36, still below the registered overall floor, while the
two bound-exhaustion cells and 4/6 membership axis independently fail the gate. The conclusion is
therefore insensitive to that adjudication.

`roster_ready` is false. The individually qualified v2 Gemma reader still lacks a second qualified
vendor/model lineage, so no new some-or-all comprehension attempt was minted and no scientific
item was shown after this holdout.
