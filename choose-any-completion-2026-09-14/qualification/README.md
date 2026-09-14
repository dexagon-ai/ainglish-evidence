# Target-independent reader qualification

The two exact cached models were screened separately on 14 September 2026 on 32 controls each
(64 cells per reader), using the official `ainglish-qualify-reader` command. Both passed. Controls resolve two unrelated
record attributes; the cold arm leaves them unknown. They contain no Ainglish selection terms,
probability-policy target questions, real target worlds or target answer keys.

This is an instrument preparation step while the author reviews the target study. It does not
approve that study, certify its statistical design, count as a proposal measurement, or supply an
independent replication. Two named families do not prove independent errors or disjoint training.

## Saved results

| Reader | Resolved controls | Unresolved controls | Qualification expires (UTC) |
| --- | --- | --- | --- |
| [Gemma 3 12B Q4_K_M](gemma-result.json) | 32/32 recovered | 32/32 explicitly said not established | 21 September 2026, 11:28:03 |
| [Mistral Small 3.2 24B Q4_K_M](mistral-result.json) | 32/32 recovered | 32/32 explicitly said not established | 21 September 2026, 11:30:10 |

The official screen scores the unresolved arm against the *resolved* answer, deliberately giving
0/32 there and establishing a detectable control gap. This is not an English-versus-Ainglish result
or a claim that a model failed 32 questions. All 128 real control cells and exact configurations are
preserved. There were **zero target cells** and no retries or model downloads.

[OBSERVATION-AUDIT.json](OBSERVATION-AUDIT.json) reproduces the counts and checks the pre-spend
screen pins, model digests, control order, configuration hashes and SDK receipt attachment.
Run `python ../audit_qualification.py` to repeat that file-only audit without inference.

## Frozen execution recipe (already executed)

The screens bind the exact local model digests, sampler settings, 128-output-token ceiling,
control order, seven-day validity and thresholds before spend. Each named configuration is run
once, with no retries or replacement chosen from outcomes. Both success and failure receipts
must be kept. Check local availability first; do not download weights or unload another user's
model. No proposal targets are run by these commands.

```sh
ainglish-qualify-reader check gemma-screen.json
ainglish-qualify-reader check mistral-screen.json
# After publishing and verifying the screens, execute each once:
ainglish-qualify-reader run gemma-screen.json -o gemma-result.json
ainglish-qualify-reader run mistral-screen.json -o mistral-result.json
```

Do not blindly rerun this recipe if result files already exist. Reuse a still-valid receipt only
with its exact bound reader/settings, or openly plan a new qualification when required. The final
target manifest must attach the validated receipt using `ainglish.reader_qualification.attach()`.
Only an actual run result can establish the qualification status; PRE-SPEND.json records plans.
