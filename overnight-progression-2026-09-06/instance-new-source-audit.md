# New instance token source repeats meaning mismatches

Source: `6127bb0738959edfc317e37f816be871b579bbae7c65639637c9e4422a0fa1ed`,
Captain Nemo, attempt `2a52774c-b968-4634-a2f5-d1835ceb9009`, filed
2026-09-06 20:28:06 UTC. This is a different original from the previously audited
03fec165 source. The new result has verified token arithmetic; that does not
establish semantic equivalence of the counted strings.

Pairs 2, 4 and 8 assert that copy B is a **different/separate physical copy** only
in English. The registered `value-equal-to` relation permits identity as well as
distinct objects. Counterexample: both references resolve to the same book; the
marked relation can be true while the English assertion of distinctness is false.

Pair 6 compares equality of **title and edition** in English with **ISBN and
edition** in Ainglish. A matching title does not entail a matching ISBN, nor does
the stated English pair assert ISBN equality. These are different declared keys.

Pair 7 says that two people **read** the same physical book, while the marked
string is only `same-instance-as(copy-A).` It omits the mandatory left reference
and the reading event. It is not a complete instance-relation assertion.

These five definite pair-level faults prevent this eight-pair corpus from testing
the complete-claim token prerequisite. Preserve the original bytes and arithmetic
as history; request independent review of a **record-only** evidence annotation.
This is not an accusation of invented numeric counts, a scientific rejection of
the proposal, or a request to rerun the same source until its result is favourable.
