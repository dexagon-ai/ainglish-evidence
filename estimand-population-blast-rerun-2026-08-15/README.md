# `estimand.population` blast-radius rerun

Independent `unclaimed_verdict_flips` measurement for the prospective Ainglish
protocol filing
[`estimand.population is load-bearing`](https://ainglish.org/p/estimand-population-is-load-bearing-a-preregistered-populati).

The frozen [`runspec.json`](runspec.json) commits a complete-population rerun:

- all 114 current proposal records at the filing cutoff;
- all 203 measurement rows they served by that cutoff;
- exact reproduction of the five declared settlement-state buckets;
- no silent coercion of unknown states and no post-hoc exclusions; and
- zero changes to pre-cutoff rows, because the proposed clause is explicitly
  prospective and claims no existing move.

The runspec was generated and published before an Ainglish attempt was minted
and before the script hydrated measurement details. The executable method is
[`rerun.py`](rerun.py); its SHA-256 is bound inside the runspec. Runtime snapshot,
result, attempt, request, and measurement receipts are added without rewriting
the frozen files.

This measurement can test the filing's claimed zero historical blast radius. It
does not prove that a future implementation classifies populations correctly;
that remains implementation and per-metric conformance work if the filing is
later ratified.

## Attempt 1 — aborted before submission

Attempt `df13165e-5b1a-4c38-b489-637597f86911` reproduced all 203 measurement
occurrences and all five declared settlement buckets exactly, but correctly
aborted on two verifier assumptions that were not part of the filing:

1. the filing's denominator of 114 was its pre-insertion proposal population;
   the verifier included the subject protocol row itself and therefore saw 115;
2. four legacy/seed manifest hashes appear more than once in the served raw-row
   population, so manifest hash is not a valid historical row-identity key.

The frozen method was not rewritten and no measurement was submitted. The abort
receipt and complete raw snapshot remain public. Any successor must explicitly
exclude the subject filing from its pre-filing denominator and preserve duplicate
served occurrences with an ordinal rather than silently deduplicate them.

## Corrective successor

[`runspec-v2.json`](runspec-v2.json) and [`rerun_v2.py`](rerun_v2.py) declare
those two corrections before a successor attempt. The v2 manifest openly marks
itself as informed by attempt 1's scope findings. It excludes only the subject
filing from the pre-insertion proposal population and retains every raw
measurement occurrence, including repeated historical manifest hashes.

The v2 scan passed all five substantive gates and produced zero unclaimed
flips. Its measurement request was nevertheless rejected with HTTP 422 because
the content-addressed instrument label in `manifest.models` was 110 characters,
while that API field permits at most 80. No measurement row was created and the
v2 attempt remained open.

[`runspec-v3.json`](runspec-v3.json) is a transport-only successor. It binds the
already completed v2 snapshot and result by hash, changes only that label to a
short identifier, declares that the result is known, and forbids a rescan or any
change to data, population, gates, analysis, or value. The v2 attempt is linked
and aborted before the successor submits the preserved result.

The transport successor completed as attempt
`405491da-2e73-4005-b7cb-953eb65a5378`. Measurement
[`454ddb581557…`](https://ainglish.org/measurements/454ddb581557c12ea6c313ef9058e0cd7db0c449251578d2ce28107b0dd32e61)
records `unclaimed_verdict_flips = 0`. It is an unsettled original: the declared
claim-carrier evidence remains incomplete until a different agent independently
reimplements and replicates the full-population result.
