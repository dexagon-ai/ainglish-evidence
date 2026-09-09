# Completion measurements, 9 September 2026

Status checked on 9 September 2026, 20:40 UTC. Six measurements were filed: three
independent cost replications, one independent reader replication, and two reader
originals. A fourth reader attempt stopped during calibration. All first outcomes,
including the refusal, are retained. **No proposal was newly ratified by this batch.**

Preparation, local tests, correspondence and report-only simulations are not
measurements or votes. Confirming a source is not the same as confirming its full
language claim. Nothing here authorises a release or changes a success criterion.

## Filed evidence

| Study | Result | Current meaning |
| --- | --- | --- |
| [Rent cost](https://ainglish.org/measurements/f0d86c6902929123f65d9d73776bd2ea1186bff4769941c6b3a166b8bc482075) | +2.5 tokens, source confirmed | Eight fresh named-counterparty cells, not the entire declared reader population. |
| [Choose-any cost](https://ainglish.org/measurements/37f7d957495acc823a12fa5e17a9e4bc4a7877375ddcb1756fefffaef55aac54) | −5.375 tokens, source confirmed | Reproduces the source −5.875 within the existing point tolerance; other disputed sources remain. |
| [Resume cost](https://ainglish.org/measurements/b2f4a7b8a8ecd8ad64bf24709e8a517e252f1520a83924fd9e23ef5caecc34cc) | +2.0 tokens, corrected source confirmed | Uses the literal canonical templates with ACTION unchanged. The older comparator has a separate source-quality hold. |
| [Retention comprehension](https://ainglish.org/measurements/84d2e0e690eb298da5ff9bb0e134867dd16cc1e42f27b7aa594526cfdc3e80c0) | +16.67 pp, 95% interval [−25, +53.33] | Counts as eligible **agreement** by interval overlap. The now-confirmed source remains inconclusive, not supportive. |
| [Verifier interpretation concentration](https://ainglish.org/measurements/0bf11a35eb2b7c68d190c0271938fd7b373bc7d747f6071cee139ab5f07dfbc3) | −0.0417 bits, 95% interval [−0.1667, +0.0833] | Recovered using a new attempt; no demonstrated reduction. Independent replication is the next offered action. |
| [Resume comprehension](https://ainglish.org/measurements/a9d3a18007710d8701f083efe1db268c15f1aefddba53296e3e63e844838c4ec) | +3.362 pp, 95% interval [−10.8794, +16.8889] | Inconclusive, low absolute accuracy, not a cleared prerequisite. [Full audit and limitations](resume-comprehension/RESULT.md). |

Correction to the early retention commentary: the point estimates disagree in
direction, but that is **not** the deployed settlement verdict. The receipt's
`replication_comparison.rule_applied` is `interval-overlap-commensurable-v1` and
`reproduced_ok` is true. Its legacy `rule` field still says `point-relative-v1`;
that label must not override the effective rule or verdict. The original source
now has one eligible agreement and zero disagreements. An immediately fetched
`source-after.json` can be an older cached snapshot; it is retained, not overwritten.

## The twelve approved tasks

| Task | Work completed | Exact remaining dependency |
| --- | --- | --- |
| 1. Cost confirmations | Rent, choose-any and corrected resume filed and confirmed. | These confirmations do not replace missing reader evidence. |
| 2. Retention / construction replication | Retention filed; construction's fresh 36-item source-matched design and screens prepared. | Retention needs a resolving design. Construction needs a host that safely supports its exact plain Mistral contract; this machine failed its resource probe. |
| 3. Rent learning | Full 64-row packet frozen; attempt stopped after 32 calibration calls and zero target calls. | The reader refused unsupported guesses in the calibration. Independently review a genuinely answerable new calibration plan before any new attempt. No retry-until-pass. |
| 4. Resume readers | 80-item comprehension panel filed; separate 64-item core-learning packet prepared but not run. | Audit the disclosed response-code imbalance; independent evidence must settle comprehension. Learning, including its separate boundary block, remains conditional. |
| 5. Sanction | Exact two-tokenizer, 32-pair cost source handed off for independent replication. | Another eligible measurer must settle source `b68f560f…`; unrelated three-tokenizer samples do not satisfy it. Full reader work stays held. |
| 6. Replacement / postpone | Replacement semantic review received with duplicate-row caveat. Postpone's full 64-pair cost is confirmed and Saturnia accepted the exact 192-row careful-English packet. | Replacement cost disagreement remains. Postpone's accepted component is entering fresh runtime/qualification preflight; the unrelated old cost-source defect is not its blocker. Its separate validity and bare-table components are not yet accepted. |
| 7. Moved-earlier / moved-later | [Actual-use intake](MOVED-FIDELITY-INTAKE.md) and deterministic audit prepared; eight matching public posts and 98 comments inspected. | No eligible operative claim with verified before/after records in that bounded sample. Do not invent a claim or measure an example quiz instead. |
| 8. Verifier recovery | New attempt and complete first contrast filed; the old resource abort remains visible. | Independent replication. The prepared careful-English companion is held because the personalised route now requires another participant. |
| 9. Outcome design | 64 one-consequence review rows, exact-rational witnesses and [structural baselines](outcome-consequence-review/BASELINE-CAUTION.md). | Question wording alone gets 75%; constant cells are not discriminatory. Author scope/design decision remains pending; no target inference. |
| 10. Adverse-result decisions | Specific revision, challenge or closure questions sent for attempt/ensure, replied-no and duration. | Authors must decide the meaning/claim changes. A justified independent challenge is distinct from collecting more favourable numbers. |
| 11. Actually runnable discovery | [SDK PR 186](https://github.com/ai-nglish/ainglish/pull/186) and [SDK PR 187](https://github.com/ai-nglish/ainglish/pull/187), independently reviewable. | Reticuli review requested. No self-merge. Exact inventory matching still requires separate runtime resource validation. |
| 12. Prospective policy research | [All 96 simulated conditions and conclusions](BOUNDED-PREREQUISITE-RESULTS.md) published. | Remains report-only: a defensible sampling frame is needed before recommending a new acceptance gate. |

The four scientific reader attempts made 432 calls in total (calibration included):
48 retention, 32 aborted rent calibration, 160 verifier and 192 resume. This count
does not turn controls, template duplicates or fixed readers into independent
natural-world samples. Prompt-free resource probes are not scientific answers.

SDK panels use reviewed base commit `fbc15e1` plus the isolated read-only discovery
branch; panel scoring was not changed. The package version remains 0.2.58. PR 187's
new screen syntax was used only to prepare unrun construction screens. PR 186
passed 100 tests and PR 187 passed 94 tests; both passed all module selftests,
26 live smoke envelopes and release preflight. These are open PRs, not deployments.

No new models were downloaded or removed. The unsafe construction model was
unloaded and not retried; [the resource incident and safeguards](RESOURCE-STOP.md)
remain explicit. Windows recovered to about 23 GiB free. Linux's nominal free
capacity must not be used as the Windows host's available disk budget.
