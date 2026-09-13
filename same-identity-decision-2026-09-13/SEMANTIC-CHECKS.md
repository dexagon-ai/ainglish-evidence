# Semantic audit before writing gold answers

These are **public design-review examples, not experimental or replication
inputs**. They contain answer information and must be excluded from the future
fresh bank. No model was queried. The expected readings below are proposals for
review; the contested same-name case needs the author's explicit disposition.

| ID | Form/context | Consequence the gold must distinguish |
| --- | --- | --- |
| O1 | Two direct handles reach a same-one editable appointment book. | Updating the referenced book changes the book available through either handle; there is no second copy to update. |
| O2 | A same-one shared original is distinguished from an earlier printed extract. | Changing the original does not establish that the historical extract changed; sharing the original is not sharing every derivative. |
| O3 | Two services share same-one lookup data but maintain explicitly separate local counters. | Shared data identity does not imply shared counter state. Name the scope of identity. |
| O4 | One referent is reached through two different display labels. | Identity need not depend on the labels matching; label difference does not create two objects. |
| K1 | Distinct same-kind price lists are checked for listed amounts at a named observation time. | A later change to one list does not itself change the other; content equality was bounded by the named check/time. |
| K2 | A same-kind claim names a field-value check while comments and formatting are explicitly outside that check. | It does not establish matching comments, formatting, byte sequences or signatures. Do not upgrade the relation. |
| K3 | A dated same-kind observation is followed by an edit to one member with no recheck. | The historical verification remains a historical fact; present equality is not established. Unknown is not automatically unequal. |
| K4 | The message calls two objects same-kind but supplies no equality check. | Category resemblance or testimony must not be credited as verified equality under an invented relation. |
| K5 | The check is named but the observation time is absent. | Do not invent an observation point or silently treat it as current. Confirm that this incomplete form is covered by the intended underspecification rule. |
| K6 | The time is named but the comparison relation is absent. | Do not invent byte, behavioural, structural or semantic equivalence. |
| K7 | Objects belong to the same ordinary category but their contents have not been compared. | Ordinary category membership alone does not justify the registered verified-content claim; this tests the misleading everyday reading of "same kind". |
| K8 | The objects were distinct and equal under a complete declared check/time. | Equality does not merge them into one entity, and a copy cannot be promoted to identity by another successful equality check. |
| N1 | Only same-name identifier matching is asserted; no identity, storage or synchronisation facts are given. | Content equality is unclaimed. Whether edits affect the other reference is not settled by this weak claim alone. **Author decision required:** prediction currently hard-codes no-propagation. |
| N2 | Both arms explicitly say the two same-name objects are distinct and unlinked. | Non-propagation follows from the common context, not from an unstated stronger definition of same-name. |
| N3 | Same-name objects have not had their contents compared. | "Not established equal" must not be scored as "established unequal". |
| N4 | Independent context later supplies a successful dated check on distinct same-name objects. | That context can support the checked equality relation; the weak name claim did not itself provide it and the objects remain distinct. |

The same-name issue is an entailment question, not an allegation that the proposal
has already failed a reader experiment. The rationale describes separate objects,
but the quoted mapping only asserts identifier matching and withholds equality.
We should agree whether distinct/unlinked objects are an explicit scope condition
or whether a stronger meaning is intended. Test materials must not repair that
choice invisibly.

Across all cases, distinguish what the message claims, what the recipient can
infer, and what an experimenter's private world ledger happens to record. A
bare-arm reader who cannot know a hidden relation is not thereby reasoning
incorrectly. The full study needs both correct operational consequences and a
truthful account of information available in each arm.
