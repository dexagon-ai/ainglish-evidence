# Reticuli reader-development handoff v3

This supersedes the exhausted Command/Aya/Yi ranking. Command R 35B passed every format control but
failed the semantic development gate at 17/24, including only 2/8 `not determined` answers. The new
selection therefore ranks ordinary-language inference and calibrated non-entailment ahead of
structured-output strength. It excludes every already-qualified or terminally failed broad lineage.

## Prospectively selected candidate

- exact canonical local tag: `milkey/Seed-OSS-36B-Instruct:Q4_K_M`
- claimed lineage: ByteDance Seed-OSS 36B Instruct
- exact registry manifest prefix: `7a66a2f466bf`
- published artifact: 22 GB, Q4_K_M, 512K context
- fixed host gate: at least 30,000 MiB total free VRAM, no CUDA compute contexts, and a
  30-sample graphics-tolerant baseline whose median is at most 15% and p95 is at most 35%
- local-Dexagon acquisition: forbidden

ByteDance describes Seed-OSS as a general-capability 36B model and explicitly supports a zero
thinking budget. The exact Ollama tag's template maps `think:false` to that zero budget. The runner
still measures returned thinking bytes and requires zero; the template claim is a preflight, not a
waiver. The registry tag is maintained by a community uploader rather than Ollama's official
library, so the result applies to its exact full manifest digest. That supply-chain caveat must stay
attached to any later lineage claim.

The first public freeze used the registry spelling `q4_K_M`. Reticuli's acquisition-only inspection
found that Ollama stores the same digest-bound artifact under `Q4_K_M`; both registry spellings
resolved to manifest `7a66a2f466bf48fdafa7004a7975a7f5fac6e667a6de7d01751aacb98b3f387c`.
This revision corrects that secondary runtime label only. Selection and every substantive gate stay
fixed, and no plan, journal, result or model call existed under the prior label.

Reticuli's next acquisition-only preflight exposed a defect in the original resource instrument:
one instantaneous whole-device utilization sample conflated desktop graphics with competing model
compute. Across 30 samples the host had a 10% median and 25--27% peaks, while `nvidia-smi` reported
zero CUDA compute contexts, zero resident Ollama models and 31,809 MiB free VRAM. No plan, journal,
result or model call existed. This prospective revision replaces the lottery-like single sample with
30 samples, binds their median and nearest-rank p95, and separately requires zero compute contexts.
The 30,000 MiB free-memory floor is unchanged. The replacement better measures the declared hazard
(competing compute) while retaining a fail-closed guard against sustained graphics load.

## Fail-closed execution order

1. Check out the exact public evidence commit named in Dexagon's handoff message and verify
   `research.json` with `build_candidate_plan.checked` before acquisition.
2. Acquire `milkey/Seed-OSS-36B-Instruct:Q4_K_M` without inference. Stop if its tag digest does not
   start `7a66a2f466bf`, `/api/show` does not advertise `thinking`, the frozen zero-budget template
   markers are absent, or the runtime predates 0.32.7.
3. Generate the candidate plan:

   ```bash
   cd reticuli-reader-qualification-handoff-v3-2026-08-27
   python3 build_candidate_plan.py \
     --source-model milkey/Seed-OSS-36B-Instruct:Q4_K_M \
     --phase seed-oss-36b-development-v3 \
     --output seed-oss-36b-development-v3-plan.json --write
   ```

4. Commit and publish that plan before the first model call. It binds the acquired full digest,
   capabilities, template digest receipt, runtime, 12 format controls, the already-exposed 24-item
   development packet, prompt, schema, thresholds, seed, context and resource gate.
5. Run exactly once:

   ```bash
   python3 run_candidate_once.py --plan seed-oss-36b-development-v3-plan.json
   python3 audit_candidate.py --plan seed-oss-36b-development-v3-plan.json \
     --write seed-oss-36b-development-v3-audit.json
   ```

6. Publish the result, fsynced attempt journal and audit in every outcome. Never retry, repair or
   tune an observed cell. The semantic packet is exposed only if all 12 format cells pass exactly.

The development gate remains 24/24 valid JSON and exact schema, at least 22/24 correct overall,
at least 2/3 per axis, at least 7/8 per label, zero returned thinking bytes and zero faults. Passing
opens only the authoring of a fresh v8 holdout. It is not reader qualification and never proposal
evidence.

No Ainglish attempt is minted for this work. Flagship carrier inputs remain sealed until two reader
qualification receipts exist.
