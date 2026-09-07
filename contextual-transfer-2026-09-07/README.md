# Contextual teaching, then structural transfer

Prospective same-author research, not a proposal measurement or release dataset.
No result is claimed by this design. The previous mixed/adverse training studies
remain published and unchanged.

Train two fixed paired conditions at each of seeds17 and29:576 contextual language
examples plus192 identical ordinary-English rehearsal examples per arm. Both arms
use the same questions, answer positions and scope notes, with only the language
surface changing. Keep the existing cached Qwen2.5-7B weights and tokenizer. One
epoch, batch2/accumulation8 and rank16 LoRA are fixed in PLAN.json. These multiple
changes do not isolate why a result might differ from earlier studies.

All four adapter receipts must be published before any target evaluation. Evaluate
the base and four adapters on192 paired semantic cases (24 authored structural
frames, eight domain/configuration realizations each) plus96 ordinary-English
retention items. Twelve neutral format controls qualify each condition separately;
failed conditions receive no targets or invented zero score. The maximum is2,400
target calls plus60 controls, retained with exact token IDs and durable intents.

## What is structurally harder here?

The simple teaching set asks one direct question. The new holdout asks whether two
conclusions follow while tracking quoted addressees, earlier versus current
decisions, exact deadline events, separately binding constraints, whole actions
versus substeps, and committed or invalid instruction updates. Unknown conclusions
are not silently treated as false facts: the answer says only whether they are
warranted. These are authored teaching-relative holdouts, not claims of globally
unseen ideas, independent test authors or hundreds of unrelated task structures.
No glossary is appended, but both arms receive task-local facts and relevant ledger
boundary rules. Do not describe these as wholly unassisted language understanding.

## Interpretation and safety

- Report both seeds, every family and all failed point screens. A stronger aggregate
  does not cancel a weaker family. A minus5-percentage-point screen is not a
  statistical proof of non-inferiority.
- Report matched-English training and English retention separately. English is the
  incumbent in these weights and tokenizer; small adapters do not simulate future
  large-scale pretraining or a new tokenizer.
- Ordinary-English rehearsal and retention use related authored families with
  different numbers and labels, not an external benchmark.
- Wait for physical GPU0 to be idle, at least14GiB available host RAM and15GiB free
  on the physical Windows volume. No downloads, cached-model deletion or eviction.
- Stop on uncertainty. Never replay an inference call, overwrite an adapter intent,
  add epochs after seeing answers, or select a favourable seed.
- Inputs/code are frozen and published before allocation. Adapters are local small
  artifacts; public receipts pin their digests. No full model checkpoints are saved.

Commands: `build.py` once; `test_design.py` and `audit.py`; publish the freeze;
`run.py train --seed <17|29> --language <ainglish|english>` for each fixed arm;
`run.py seal`; publish the seal; `run.py evaluate`; `analyse.py`.
