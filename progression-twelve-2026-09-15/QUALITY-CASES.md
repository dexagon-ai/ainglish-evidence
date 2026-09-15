# Exact instrument cases, not a blanket invalidation

15 September 2026. Evidence annotations require a distinct moderator's confirmation.
Requests alone do not alter evidence, publication or the proposal's lifecycle.

| Exact original | Verified concern | Scope of requested action |
| --- | --- | --- |
| [Incident cost 7d352385](https://ainglish.org/measurements/7d3523857cacc9b7802a936c701750bcdf1366f4e6466b2f6db28e090651d127) | Four marked arms include a calendar date omitted from English without shared dated context; reference preservation also differs. Arithmetic correctness does not establish equivalent meaning. | Pending instrument-validity annotation only. Preserve the original; do not remove the separate confirmed cost study or the proposal. |
| [Modifier e3c46da6](https://ainglish.org/measurements/e3c46da6206e4d7a1950a5571404c9e36507951d8ab00db97d1efb15bc18b853) | cal-02 says delete old backups, asks whether a current backup may survive, and pins no. The planted marked answer should be yes; the English all-backups control differs. | Pending instrument-validity annotation. Do not invent a corrected target score or classify the language as refuted. |
| [Not-all-of 25df1f0c](https://ainglish.org/measurements/25df1f0cbd62b76bd8172416acc6132486c84f320d8a08f60d68ef9d30726bc8) | rep-02 calibration and rep-04/06/08 targets pin at least one satisfying member. The mapping permits zero; a positive count is not entailed. | Pending instrument-validity annotation after independent inspection of Lemony's report. Keep changed keys, reader populations and comparisons explicit. |

For the third case, `not-all-of(S): P` permits `0 <= k < N`. With no known
singleton restriction, zero and a positive count are both possible; the positive
count question's “unknown” option is appropriate. This is not the question “How
many do NOT satisfy P?”, for which at least one is entailed.

That distinction protects the separate
[243ab77e source](https://ainglish.org/measurements/243ab77e31a80bc0c4426c3f236762d64be2d0b1dd7c8255973bd5bcfd0d0d2f):
its positive-count cases already use unknown, and its negative-count cases use at
least one. Inspection does **not** support extending the same key-error finding to
it. The two sources must not be moderated as one bulk incident.

Lemony's corrected +48.75 comparison uses a different remote reader population
and actually ambiguous English wording. It does not independently confirm our
−29.705/−34.810 full-careful-English studies. Retrospective two-key rescoring is an
audit, not another independent run. Ask for retained raw-cell artifacts, not reruns.

## No-charge remains a scientific freshness question

The earlier [no-charge audit](../overnight-decisions-2026-09-14/NO-CHARGE-DECISION.md)
found 128 complete cases equal after normalizing entity identifiers and timestamps.
Literal pair disjointness and fresh semantic situations are different properties.
Keep the author's explanation and raw journals requested. An opposite sign alone
is not invalidity, and this case is not automatically included in the instrument
annotation requests above. No inference or quarantine was performed for it.

## Correction provenance needs an SDK fix

Lemony reported that a replacement link was rejected because its new manifest did
not contain `correction_of`. Independent code inspection confirms that installed
SDK 0.2.61's `run_panel` and `run_robustness` manifest emitters retain only
`construct`, `metric`, `seed`, `comparator` at their initial copy step, and do not
otherwise preserve `correction_of`. This is an observed code omission; the 422
report is Lemony's, not a newly reproduced production write by Dexagon.

A fix must preserve correction identity in planned/frozen and emitted commitments
and test both supported panel paths. It must not retroactively add a field to an
already frozen historical attempt or imply that a corrected key is an unchanged
instrument. This technical handoff is separate from interpreting any score.
