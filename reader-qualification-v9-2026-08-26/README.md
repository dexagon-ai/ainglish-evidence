# Reader qualification v9: distinct Liquid-family prospect

This package is instrument qualification only. It is never Ainglish proposal evidence.

The prospective candidate is Liquid AI's LFM2 24B-A2B, a hybrid model family that is distinct
from the sole v8 qualifier, Qwen 3.6 35B. The exact Ollama manifest, served capability set,
runtime, prompt, transport, and already-exposed v8 development packet are bound in a digest-pinned
plan before the first candidate call.

The candidate must first pass the frozen 12-cell structured-output gate. Only then may it see the
24-cell ordinary-English development packet. Passing requires 24/24 schema-exact responses, at
least 22/24 correct, at least 2/3 on every semantic axis, at least 7/8 for every answer label, zero
thinking bytes, and zero faults. No prompt, sampler, wrapper, or failed cell may be retried after
observation.

A development pass is not qualification. It only permits a later, newly authored, disjoint
holdout. The holdout and both reader plans must be committed and pushed before either LFM2 or the
already-qualified Qwen reader sees a holdout item. Both distinct lineages must pass the unchanged
qualification gate before a scientific roster is released.

After the exact candidate is installed, freeze its plan with:

```bash
python3 build_development_plan.py
```

Then commit and push the generated plan and index before running:

```bash
python3 run_candidate_once.py --plan development-lfm2-plan.json
python3 audit_candidate.py --plan development-lfm2-plan.json --write development-lfm2-audit.json
```

The runner is one-shot by construction: an existing journal or result refuses execution.

## LFM2 outcome

LFM2 passed the structured-output gate at 12/12 exact responses, with zero thinking bytes and zero
faults. It failed the exposed semantic development gate at 16/24 rather than the required 22/24.
The largest failure was `not determined` at 2/8; quantifier force and set membership were each 1/3.
The offline journal/result auditor passed without correction.

This is a terminal retained development failure. LFM2 received no holdout item and no Ainglish
scientific carrier. The two-lineage roster remains closed at 1/2. The prospectively selected Yi
reserve may now activate under a separately frozen exact-manifest plan; LFM2 will not be rerun under
a different prompt, sampler, wrapper, or quantization.

After `yi:34b` is installed, freeze the activated reserve with:

```bash
python3 build_yi_reserve_plan.py
```

Commit and push `development-yi-reserve-plan.json` and `reserve-index.json` before the first Yi
call. Yi then receives the same one-shot format and exposed development gates through the existing
runner and auditor.

## Yi reserve outcome

Yi passed the structured-output gate at 12/12 exact responses, with zero thinking bytes and zero
faults. It failed the unchanged exposed semantic development gate at 20/24 rather than the required
22/24. The per-axis floor was met, but the `not determined` label reached only 4/8 rather than 7/8.

This is a terminal retained development failure. Yi received no holdout item and no Ainglish
scientific carrier. It will not be retried or tuned on the exposed cells. The two-lineage roster
therefore remains closed at 1/2, so all reader-dependent proposal work stays gated.
