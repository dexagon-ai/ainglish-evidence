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
