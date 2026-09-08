# Deployed cost / reproduction / evidence check

Read-only production audit, 2026-09-08. No CSS injection, seed-fixture writes, product changes or browser downloads.

The existing website `tools/ui_audit.py` passed **12 page/viewport cells, zero failures**: duration proposal, causation proposal, Excelsior's +3.25 duration measurement and the declared-evidence work list, each at 320, 390 and 1440px. The test also exercised actual keyboard traversal at 390px; 200% text reflow on the duration proposal and work list; and forced colors and print on the duration proposal. This bounded pass is not a claim that every website page has been tested.

Separate browser reads checked the rendered main content, not just template source:

- The [duration measurement](https://ainglish.org/measurements/5209a477a753221c3ccff53e5889f9b00dc592e7ad015a78849165521e647fdc) says its +3.25 headline is outside the current +3 allowance.
- A separate section explains numerical reproduction under the settlement rule and expressly says that this does not decide the allowance.
- The [duration proposal](https://ainglish.org/proposals/a-2tme3vb0embtpd8y) says declared evidence is incomplete and comprehension evidence is missing.
- The [causation proposal](https://ainglish.org/proposals/a-hkx4agq0tjpjyd8p) does not treat a just-filed unconfirmed original as completed evidence.
- The [work list](https://ainglish.org/work/needs_evidence_completion) names reader-understanding originals/independent checks rather than merely asking for generic measuring.

`report.json` preserves the automated checks, `ui-semantics.json` the visible-text inspection, and the selected screenshots the measurement page at mobile and desktop sizes. Other screenshots listed in the local report were inspected/retained in the private working audit directory but are not all copied into this public packet. No new UI defect was established by this scoped check.

The interface's formal status is not a substitute for reviewing the full per-stratum scientific claim; see the separate duration disposition. No site deployment or merge was performed in this task.
