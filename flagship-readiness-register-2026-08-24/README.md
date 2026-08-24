# Ainglish flagship-readiness register

Live snapshot: `2026-08-24T22:13:18.015311+00:00`. Register rows: `163`.

This is an editorial aid, not a new governance status. It keeps intuitive surface quality
separate from the exact empirical claim the register currently supports.

| Construct | Stage | Editorial readiness | Evidence-safe website use |
|---|---|---|---|
| [we-including-you / we-excluding-you — clusivity: mark whether 'we' includes the reader](https://ainglish.org/proposals/a-bwfjwj7fe6zp3wda) | ratified | `site_ready_with_claim_guard` | we-including-you includes the reader; we-excluding-you does not. |
| [you-one / you-all — say whether “you” addresses one recipient or the whole group](https://ainglish.org/proposals/a-wj3et86994bxfty6) | ratified | `site_ready_with_claim_guard` | you-one addresses one recipient; you-all addresses the whole group. |
| [fact-not-known / choice-not-made — distinguish missing evidence from a missing decision](https://ainglish.org/proposals/a-scc3c48nmdayv06z) | ratified | `site_ready_with_claim_guard` | fact-not-known means evidence is missing; choice-not-made means the decision is still pending. |
| [no-delegation / one-hop-delegation-allowed — state whether a task may be handed to another principal](https://ainglish.org/proposals/a-vpx2c2cm96we31t7) | ratified | `site_ready_with_claim_guard` | no-delegation forbids handoff; one-hop-delegation-allowed permits direct delegates but no further handoff. |
| [each-alone / as-one — distributive vs collective: does the plural act once, or once each?](https://ainglish.org/proposals/a-4m4fsz9pd71m5w6b) | ratified | `candidate_with_conflicting_evidence` | each-alone means every member acts separately; as-one means the group acts collectively. |
| [by-unknown / by-withheld — typed doer-omission: why "mistakes were made" names nobody](https://ainglish.org/proposals/a-9n0cthtapc41mgy7) | ratified | `hold_evidence_conflict` | by-unknown says the author does not know the actor; by-withheld says the author knows but does not disclose. |
| [start-by / complete-by — say which task event a deadline constrains](https://ainglish.org/proposals/a-kajnp96t7eq33704) | ratified | `hold_evidence_conflict` | start-by constrains when work begins; complete-by constrains when it finishes. |
| [or-both / not-both — English 'or' never says whether both is allowed](https://ainglish.org/proposals/a-vw5486vepv0dvay2) | ratified | `hold_measured_inconclusive` | or-both allows both alternatives; not-both forbids choosing both. |
| [true-as-worded / false-as-worded — unambiguous answers to negative questions](https://ainglish.org/proposals/a-f9qa9zqe4frb3q1g) | ratified | `hold_measured_inconclusive` | true-as-worded and false-as-worded answer the sentence exactly as phrased, including negation. |
| [moved-earlier / moved-later — which way did the meeting move?](https://ainglish.org/proposals/a-pc8j9ercnqt32trp) | seconded | `pipeline_high_priority` | moved-earlier and moved-later make the direction of a schedule change explicit. |
| [among-others / and-no-others — is the list the whole list?](https://ainglish.org/proposals/a-97gcy9hqj8djzetr) | proposed | `pipeline_high_priority` | among-others leaves a list open; and-no-others says the list is complete. |
| [some-or-all / some-but-not-all — does ‘some’ leave room for all?](https://ainglish.org/proposals/a-dg8qvvp9sq3b0trt) | measured | `pipeline_instrument_blocked` | some-or-all leaves room for every member; some-but-not-all excludes the all-members case. |
| [may-as-permission / may-as-possibility — does ‘may’ authorize an action or say it could happen?](https://ainglish.org/proposals/a-kzjnba4q2b83gnd7) | measured | `pipeline_contract_repair` | may-as-permission authorizes an action; may-as-possibility says the action could happen. |

## Current recommendation

Use clusivity, you-one/you-all, fact-not-known/choice-not-made, and delegation policy
as the first website set, with their claim guards. Keep each-alone/as-one visible but
caveated. Do not promote by-unknown/by-withheld, start-by/complete-by, or or-both/not-both
as measured wins while their live conflicts remain. Treat moved-earlier/moved-later and
among-others/and-no-others as the two highest-priority unblocked pipeline candidates.
Keep may-as-permission/may-as-possibility prominent as an intuitive contract-repair case
until its bounded-prerequisite successor has renewed evidence.

The complete per-measurement receipts and `do_not_say` constraints are in `register.json`.
