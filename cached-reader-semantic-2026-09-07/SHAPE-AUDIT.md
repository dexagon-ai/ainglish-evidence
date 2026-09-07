# Why the two-field scores are zero

This is a **post-hoc diagnostic**, not the declared score and not a new model run.
The [frozen results](RESULTS.json) remain unchanged.

All 24 two-field responses contained the requested values plus three unwanted
keys. The exact-key protocol therefore refused every one: **0/12 per language**.
Looking only at the two requested boolean values gives 12/12 per language, but
that projection was not the scoring rule fixed before the experiment.

[SHAPE-AUDIT.json](SHAPE-AUDIT.json) retains each case, the extra and missing
keys, and the projected-value check. [shape_audit.py](shape_audit.py) regenerates
it from the completed raw journal, refusing duplicate keys. No calls are retried.

The five-field condition is different: all 96 responses per language both met
the declared protocol and exactly matched all five values. Each language scored
32/32 in each of the three authored contexts. This demonstrates reference-assisted
reading on these cases, **not an Ainglish advantage over English**. The reused
cases, one qualified reader, visible guides and shared authorship limit the claim.

Any new output protocol needs prospective qualification. This audit does not
unlock the separate failed Qwen writer/reader gate, adapter training or a
model-driven operational benchmark.
