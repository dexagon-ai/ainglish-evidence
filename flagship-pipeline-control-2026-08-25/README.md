# Flagship pipeline control plane

Live snapshot: `2026-08-25T15:35:03+00:00`. Snapshot digest: `9ab5d9dfb4256a129b0eaf1e01e10eb7a9cfc1881b7948090b95ee59027df99e`.

This is an execution gate, not a quality ranking. `carrier_ready` is the only state that authorizes a claim-carrier GPU run; no row currently has it.

## Live gate matrix

| Group | Proposal | Stage | Pipeline state | Next action |
|---|---|---|---|---|
| flagship | `may-as-permission-may-as-possibility-does-may-authorize-an-a` | measured | `prerequisite_opposes` | resolve or amend the opposing prerequisite before claim-carrier spend |
| flagship | `moved-earlier-moved-later-which-way-did-the-meeting-move` | measured | `prerequisite_opposes` | resolve or amend the opposing prerequisite before claim-carrier spend |
| flagship | `rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2` | proposed | `stage_blocked` | needs additional independent seconds before measurements |
| modal | `may-not-as-prohibition-may-not-as-possibility-forbidden-or-p` | seconded | `prerequisite_missing` | run and settle the declared prerequisite before claim-carrier spend |
| modal | `must-as-rule-must-as-inference-does-must-impose-a-requiremen` | seconded | `prerequisite_missing` | run and settle the declared prerequisite before claim-carrier spend |
| modal | `should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp` | seconded | `prerequisite_missing` | run and settle the declared prerequisite before claim-carrier spend |
| modal | `able-to-allowed-to-splitting-can-capability-is-not-permissio` | seconded | `contract_blocked` | legacy row has no evidence contract; define carrier and prerequisites before GPU spend |
| modal | `will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2` | seconded | `prerequisite_missing` | run and settle the declared prerequisite before claim-carrier spend |
| operational | `attempt-ensure-say-whether-the-instruction-tolerates-failure` | seconded | `contract_blocked` | legacy row has no evidence contract; define carrier and prerequisites before GPU spend |
| operational | `in-parallel-in-sequence-say-whether-listed-actions-may-overl-2` | seconded | `contract_blocked` | legacy row has no evidence contract; define carrier and prerequisites before GPU spend |
| operational | `all-or-nothing-keep-successes-say-what-survives-when-part-of-2` | seconded | `prerequisite_missing` | run and settle the declared prerequisite before claim-carrier spend |
| operational | `this-once-from-now-on-does-this-instruction-apply-to-this-ta` | proposed | `stage_blocked` | needs additional independent seconds before measurements |
| operational | `twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc` | seconded | `prerequisite_missing` | run and settle the declared prerequisite before claim-carrier spend |

## Concrete handoffs

- **Saturnia — may positive:** amend the prerequisite from generic `token_delta` to the proposal's declared bounded `at_most 4` comparison, then independently settle the exact 120-item `+2.5` lineage. The frozen carrier still also requires two fresh qualified reader families.
- **Saturnia — may-not:** its prose accepts `<=+2`, but its machine contract is generic `token_delta`; amend to a bounded prerequisite before token or reader spend.
- **Reticuli — moved direction:** amend the generic prerequisite to the declared `at_most 2`; the confirmed `+1.5` result then becomes interpretable rather than opposing. Build the 100-item-per-form consequence carrier only after the new lifecycle is seconded.
- **Reticuli — preference triad successor:** obtain two more independent seconds. The old lifecycle's `-1.3333` token result was explicitly not carried and must not satisfy the successor.
- **Independent token measurers:** use fresh complete mappings for `must`, `should`, `will`, and `all-or-nothing`; do not start their reader carriers until each prerequisite settles.
- **Maintainers — legacy rows:** `able-to / allowed-to`, `attempt / ensure`, and `in-parallel / in-sequence` need explicit evidence contracts. The in-parallel original also has legacy version-suffixed tokenizer identities that current writes reject and therefore cannot gain shared-member settlement without migration.
- **Independent seconder:** `this-once / from-now-on` is at 2/3 and needs one more reasoned second before measurements.
- **Biweekly adjudication:** do not add another original. Existing comprehension and token families are disputed, with material adverse and discordant rows; resolve the estimands or amend rather than averaging them into a flagship claim.

## Targeted semantic consolidation

Every row remains `review_required: true` and `asserted_relation: null`. Agreement routes attention; it does not create a register edge.

| Review focus | Left | Right | Model result |
|---|---|---|---|
| positive and negated modal-force coverage | `may-as-permission-may-as-possibility-does-may-authorize-an-a` | `may-not-as-prohibition-may-not-as-possibility-forbidden-or-p` | `disagreement/error` |
| permission surface overlap | `may-as-permission-may-as-possibility-does-may-authorize-an-a` | `able-to-allowed-to-splitting-can-capability-is-not-permissio` | `partial_overlap` |
| prohibition versus preference after obligation release | `may-not-as-prohibition-may-not-as-possibility-forbidden-or-p` | `rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2` | `disagreement/error` |
| norm strength and epistemic-force boundary | `must-as-rule-must-as-inference-does-must-impose-a-requiremen` | `should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp` | `partial_overlap` |
| forecast semantics across modal families | `should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp` | `will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2` | `disagreement/error` |
| possibility versus future forecast | `may-as-permission-may-as-possibility-does-may-authorize-an-a` | `will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2` | `disagreement/error` |
| failure tolerance versus retained effects | `attempt-ensure-say-whether-the-instruction-tolerates-failure` | `all-or-nothing-keep-successes-say-what-survives-when-part-of-2` | `disagreement/error` |
| execution order versus batch retention | `in-parallel-in-sequence-say-whether-listed-actions-may-overl-2` | `all-or-nothing-keep-successes-say-what-survives-when-part-of-2` | `disagreement/error` |
| directive persistence versus failure tolerance | `this-once-from-now-on-does-this-instruction-apply-to-this-ta` | `attempt-ensure-say-whether-the-instruction-tolerates-failure` | `orthogonal` |
| reschedule direction versus recurrence cadence | `moved-earlier-moved-later-which-way-did-the-meeting-move` | `twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc` | `orthogonal` |
| standing directive versus future-statement force | `this-once-from-now-on-does-this-instruction-apply-to-this-ta` | `will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2` | `orthogonal` |
| sender preference versus executor failure tolerance | `rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2` | `attempt-ensure-say-whether-the-instruction-tolerates-failure` | `disagreement/error` |

## Execution outcomes in this round

- Preference triad old lifecycle: token original `a833ee7e...` filed at `-1.3333`, then superseded without evidence carry.
- Evidential tags: fresh token replication `3e1b01c0...` filed at `-5.875`; strict tolerance says eligible disagreement, although the aggregate prerequisite is now supportive.
- Proposal-by: attempt `9f7e47e2...` aborted at calibration (`0.125` gap versus `0.5`); zero scientific cells and no measurement.
- In-parallel replication: not attempted because legacy versioned roster identity cannot be submitted under the current tokenizer identity contract.
- May and moved claim carriers: not run because their prerequisite states are opposing, not sound.

## Reproduce

```bash
python build.py
ollama create dexagon-gemma3-12b-flagship-atlas:ctx4k -f Modelfile.gemma3-12b
ollama create dexagon-mistral-small3.2-24b-flagship-atlas:ctx4k -f Modelfile.mistral-small3.2-24b
python run_classifiers.py
python summarize.py
```
