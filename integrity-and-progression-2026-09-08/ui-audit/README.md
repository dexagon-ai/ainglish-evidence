# Local reader-quality UI verification

This is an isolated local rendering fixture, **not a production measurement or deployment**.
The receipt and question data come from the already-public attempt/ensure source, with the
proposal title and local identity explicitly marked as a fixture. Local proposal IDs in this
report are not public Ainglish proposal IDs.

Implementation: private ainglish-symfony PR 561, commit `c92847c`. Public explanation and
the scientific boundaries are in the [batch overview](../README.md) and
[bounded semantic review](../attempt-ensure-review.md).

`report.json` records 20 page/viewport cells over receipt, proposal, exact-result comparison
and case studies at 320, 390, 768, 1024 and 1440 px. The audit also exercised keyboard
traversal, 200% text reflow, forced colors and print. It reported zero automated failures.
The complete screenshots are retained alongside the report. A passing automated audit is
not exhaustive accessibility certification or evidence of human comprehension.

The full local PHP suite passed 1,495 tests and 24,565 assertions with no failures/errors;
six skips and three PHPUnit deprecations remain visible. Twig/container lint and CSS
ownership contracts passed. The complete suite used a 1 GiB PHP memory cap; an earlier
256 MiB invocation stopped loading tokenizer vocabulary and is not counted as a pass.
