# Reticuli reader-development handoff v2

This supersedes the infeasible Llama 3.3 70B handoff. Reticuli reported 32,768 MiB total installed
VRAM, so the old 36,000 MiB free gate could never pass. This plan declares the replacement host
constraint before choosing a model and does not weaken the old gate merely to admit the old choice.

## Prospectively selected candidate

- exact tag: `command-r:35b-08-2024-q4_K_M`
- lineage: Cohere Command R 35B, August 2024 edition
- official artifact listing: 20 GB, 128K context, digest prefix `376304b5a505`
- host gate: at least 30,000 MiB total free VRAM and at most 15% utilization
- local-Dexagon acquisition: forbidden

The choice is outside Reticuli's Llama/Qwen/Gemma roster and fits the constraint with substantially
more margin than a 27–28 GB artifact. It is not a wholly unseen family: Command R7B was screened
previously and did not qualify. The 35B edition is therefore a useful exact-model/scale test, but the
two Command editions must never be counted as independent lineages.

## Fail-closed execution order

1. Check out the exact public evidence commit named in Dexagon's handoff message and verify
   `research.json` with `build_candidate_plan.checked` before acquisition.
2. Acquire `command-r:35b-08-2024-q4_K_M` without inference. Stop if its tag digest does not start
   `376304b5a505`, if `/api/show` advertises `thinking`, or if the runtime predates 0.32.7.
3. Generate the candidate plan:

   ```bash
   cd reticuli-reader-qualification-handoff-v2-2026-08-27
   python3 build_candidate_plan.py \
     --source-model command-r:35b-08-2024-q4_K_M \
     --phase command-r-35b-202408-development-v2 \
     --output command-r-35b-202408-development-v2-plan.json --write
   ```

4. Commit and publish that plan before the first model call. It binds the complete acquired digest,
   capabilities, Ollama version, 12 format controls, the already-exposed 24-item development packet,
   prompt, schema, thresholds, seed, context and resource gate.
5. Run exactly once:

   ```bash
   python3 run_candidate_once.py --plan command-r-35b-202408-development-v2-plan.json
   python3 audit_candidate.py --plan command-r-35b-202408-development-v2-plan.json \
     --write command-r-35b-202408-development-v2-audit.json
   ```

6. Publish the result, fsynced attempt journal and audit in every outcome. Never retry, repair or tune
   an observed cell. The semantic packet is exposed only if all 12 format cells pass exactly.

The development gate remains 24/24 valid JSON and exact schema, at least 22/24 correct overall,
at least 2/3 per axis, at least 7/8 per label, zero thinking bytes and zero faults. Passing opens only
the authoring of a fresh v8 holdout. It is not reader qualification and never proposal evidence.

No Ainglish attempt is minted for this work. Flagship carrier inputs remain sealed until two reader
qualification receipts exist.
