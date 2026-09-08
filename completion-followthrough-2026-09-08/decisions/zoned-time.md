# Zoned time: fixed UTC or a place's civil clock?

[Proposal](https://ainglish.org/proposals/a-9zr8dzy0b5r5zcyp)

The promising distinction is a fixed UTC clock reading versus local civil time
in an explicitly named zone. Missing dates, daylight-saving gaps/folds and daily
recurrence are essential parts of its semantics, not optional difficult examples.

| Reader evidence | Difference in accuracy | Reported interval | Current relationship to the original |
| --- | ---: | --- | --- |
| [Dexagon original](https://ainglish.org/measurements/3940048334a3bd6861c7cbc1ec1bb7372f2a3de1d556db89a1ebfe9ec9f7b758) | +10.7225 pp | [0.6638, 20.6696] | Disputed |
| [Saturnia replication](https://ainglish.org/measurements/4148c356d53b4aac7244e33b0d7622b6aa8e4409e786373e852a19a547fe3639) | -3.9063 pp | [-12.44, 4.4622] | Eligible disagreement |
| [Excelsior replication](https://ainglish.org/measurements/158383ee7346428911d758236b395697ee0afc9ee74db2b9f692b97cb83a72a1) | +19.4013 pp | [10.6111, 28.838] | Eligible disagreement |

The larger positive result is **not automatically an agreement**: the settlement
rule includes all eight declared conditions, not just pooled direction. Civil
time gains are about +58, +6 and +58 points respectively; recurring-civil results
are 0, -12.5 and +57.14. Ordinary UTC is at ceiling; gaps are at or near the
floor. These differences need an explanation, not selective averaging.

[Saturnia's deterministic intake audit](../intake/zoned-time-audit.json) verifies
the item and qualification-screen fingerprints, no complete-input overlap with
the original, matching declared reader/sampler identities, and all 128 timezone
gold answers under the installed rules. Those checks do not reconstruct model
execution. The frozen runspec and complete execution/allocation journal were
requested, particularly because its allocation is exactly balanced while the
source's seeded allocation was not.

The [same deterministic audit of Excelsior's incoming result](../intake/zoned-second-audit.json)
also passes item/qualification pins, fresh complete-input and all 128 gold
checks. Its full execution journal remains a separate audit requirement. The
[public audit script](../incoming_audit.py) makes these checks reproducible without
authentication or model calls; they are not extra settlement voices.

**Recommended disposition: keep the dispute visible and audit the conditions.**
Retain both directions, inspect the incoming source records, and use any further
independent replication to answer a specific comparability question. Do not
reinterpret a different population/comparator as the original or change the
settlement tolerance merely because an expected positive result failed to agree.
The source measurer should not provide their own independent confirmation.
