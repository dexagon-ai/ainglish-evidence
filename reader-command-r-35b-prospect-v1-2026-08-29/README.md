# Command R 35B prospective reader seat

This package selects Reticuli's already-installed `command-r:35b-08-2024-q4_K_M` as a
no-download prospect for the missing general reader lineage. The exact digest, ordered
capabilities, model details, template length and template SHA-256 are frozen from non-answer-bearing
preflight metadata. The run wrapper verifies every field again at the host before a call.

## The adverse prior is part of the plan

Before these plans were frozen, Reticuli disclosed a same-digest refusal on a separate
`they-one / they-many` panel. Command R scored 2/6 on each calibration arm (gap 0), and the full
panel refused before buying any real cell. The public receipt is pinned at
`reticuli-labs/panel-artifacts@6c32a4a75c30c1e1feb41baba79f884857104974` and its byte digest is
bound into both plans.

That is adverse instrument evidence for that construct. It is not silently discarded, but neither
is it promoted into a claim about general English capability. The proper consequence is a stricter
order: Command R must first pass the already-exposed 24-item ordinary-English development screen.
Only then may it see the separately frozen 64-item v10 holdout. Failure at either stage is retained
and terminal; no cell, prompt, seed, token bound, wrapper, or quantization is retried.

Both stages use native structured JSON, `think:false`, and a 16-token response bound. This is not
the 1,024-token reasoning-reader configuration implicated in Reticuli's separate panel: Command R
does not advertise thinking, and the required response is one tiny JSON object. The 12-cell format
gate will fail closed before semantic exposure if that bound is nonetheless incompatible.

## Frozen execution order

1. Publish both plans, runner, audits, and this explanation before the first Command R call.
2. On the independent host, fresh-pull the public commit and run only the development plan:

   ```bash
   python3 reader-command-r-35b-prospect-v1-2026-08-29/run_once.py \
     --plan development-command-r-plan.json
   ```

3. Publish the result and append-only journal whether it passes or fails. Audit it with
   `audit_development.py --plan development-command-r-plan.json`.
4. Only if the sealed exact result has `v8_holdout_eligible=true`, run the already-public holdout
   plan once. The runner enforces that dependency mechanically.
5. Publish and audit the holdout result whichever way it lands. A pass qualifies only this exact
   lineage for general-scope carriers; it is never proposal evidence and does not satisfy a
   restricted roster merely because it is a new family.

Plan construction and static audit make no model, tokenizer, network, or governance call. No model
was downloaded for this prospect.
