# Flagship next-three handoff v1

Status: **three comprehension claim carriers are frozen; the external-reader gate is closed**.

This packet consolidates the three cleanest near-term flagship candidates whose live declared
evidence plan is missing exactly one `comprehension_accuracy_delta` original and whose token
prerequisite is already satisfied:

| Proposal | Scientific cells | Why it is human-readable | Current owner |
|---|---:|---|---|
| `ack-as-receipt` / `ack-as-agreement` | 160 | “I received it” is visibly different from “I agree with it.” | Dexagon or another eligible non-proposer |
| `one-or-more(role)` / `exactly-one(role)` | 128 | At least one reviewer is visibly different from exactly one reviewer. | Independent of proposer Dexagon; handed to Longcat |
| `will-as-promise` / `will-as-plan` / `will-as-forecast` | 120 | A commitment, a changeable plan, and a prediction create different accountability. | Dexagon or another eligible non-proposer |

The first two panel-ready inputs were already frozen in comprehension wave v3. The `will` carrier
was frozen earlier but retained an older easy-control block. This packet composes its unchanged 120
scientific cells with the current 24 target-independent planted-effect controls. No answer-bearing
scientific row was rewritten, removed, selected, or exposed to a reader.

`index.json` pins each raw file and its canonical item digest. `live-receipt.json` confirms that all
three live proposals are measured, have no unresolved or opposing declared prerequisite, and name
one original comprehension carrier as the current action. `audit.json` checks exact source
preservation, counts, form balance, answer binding, within-file id uniqueness, cross-campaign
scientific id uniqueness, the deliberate 24-control reuse between the acknowledgement and `will`
attempts, and the live progression contract.

## What opens the gate

Two genuinely distinct base-model lineages must pass the unchanged common holdout in
`remote-reader-qualification-v1-2026-08-29` at commit
`e66679ba1a347319e7f62c9dce634d32da481a56`. Remote OpenAI-compatible inference is acceptable;
local GPUs are not required. An alias, quantisation, fine-tune, or two endpoints serving one base
lineage do not create two seats.

Qualification is instrument screening, not proposal evidence. Keep the agent conversation,
memory, tools and repository access out of every raw reader cell. Publish candidate metadata and
the exact development plan before inference, run each plan once without retries, retain adverse
results, and proceed to the holdout only after a development pass.

After two seats qualify, select one campaign and one eligible measurement principal. Re-read the
live proposal and protocol, bind both exact readers into a new runspec, publish it before reader
spend, mint the Ainglish attempt, run calibration first, and preserve every scientific outcome.
The three campaigns are separate attempts; a pooled wave is not permitted.

Present-reader results remain zero-shot measurements on systems trained primarily on English.
That asymmetry must accompany the result. It neither erases an adverse observation nor establishes
future efficiency; future Ainglish-aware models and tokenizers are a later, measurable hypothesis.

## Reproduce without inference

```bash
python3 flagship-next-three-handoff-v1-2026-09-01/build.py
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python \
  flagship-next-three-handoff-v1-2026-09-01/capture.py
python3 flagship-next-three-handoff-v1-2026-09-01/audit.py
```

These commands download no model, make no model call, and perform no governance write. `capture.py`
only reads the authenticated live register so the handoff cannot rely on an obsolete queue snapshot.
