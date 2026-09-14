# Target-independent reader qualification

The two exact cached models are being screened separately on 32 controls each (64 cells per
reader), using the official `ainglish-qualify-reader` command. Controls resolve two unrelated
record attributes; the cold arm leaves them unknown. They contain no Ainglish selection terms,
probability-policy target questions, real target worlds or target answer keys.

This is an instrument preparation step while the author reviews the target study. It does not
approve that study, certify its statistical design, count as a proposal measurement, or supply an
independent replication. Two named families do not prove independent errors or disjoint training.

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
