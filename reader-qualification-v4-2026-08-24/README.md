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
