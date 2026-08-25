# Ainglish learning-curve and fluent-adapter programme

This programme builds a rights-pinned corpus from the current, non-superseded ratified register and
trains a QLoRA adapter as a product/research demonstration. It is deliberately outside Ainglish
governance evidence: one trained model is not an independent principal, training on register text
contaminates cold-comprehension measurement, and a favourable adapter benchmark cannot ratify a
construct.

The development split withholds every source row from four construct families and filters any
remaining row that contains one of their exact registered marker strings. That adapter is
evaluated for format/generalization on seen constructs and transfer on those unseen registered
surfaces. This is not a claim that all related ordinary-English concepts are absent. Only after
those results are frozen may a separate release adapter train on all 19 ratified surfaces.

Base model: `Qwen/Qwen2.5-7B-Instruct` (Apache-2.0). Dataset contribution terms and source digests
are captured in `register-snapshot.json` and `manifest.json`.

`evaluate.py` records exact predictions, token-overlap F1, and exact registered-form retrieval.
These are deliberately modest reproducible diagnostics, not claims of general language fluency.
`compare_evaluations.py` refuses split drift before reporting base-to-adapter deltas, and
`freeze_adapter.py` records a path-and-content digest for the local adapter without committing
large model weights to Git.

## Frozen development result

The development adapter trained for two epochs over 76 rows (20 optimizer steps) in 87.3 seconds.
Its mean training loss was 2.7233. The complete local artifact contains 42 files and
1,178,906,558 bytes; `adapter-artifact-receipt.json` pins those files with directory digest
`df33a8862f3542093622ba1442031583b5621faa323547826d3a408fb25646d7`.
The weights and optimizer checkpoints remain local and are not committed to Git.

On the 14-row seen validation split, mean token F1 was effectively flat: 0.221982 for the base
model and 0.222715 for the adapter (+0.000733). Across the 28-row transfer holdout, mean token F1
rose from 0.314583 to 0.345646 (+0.031062), but the task cells were heterogeneous:

| Transfer task | Base F1 | Adapter F1 | Delta |
| --- | ---: | ---: | ---: |
| definition | 0.212936 | 0.187804 | -0.025132 |
| distinction summary | 0.204052 | 0.231253 | +0.027201 |
| example encode | 0.453531 | 0.393793 | -0.059738 |
| example expand | 0.428326 | 0.276734 | -0.151592 |
| form retrieval | 0.585858 | 0.880953 | +0.295095 |
| lossless expansion | 0.076149 | 0.184900 | +0.108751 |
| scope and constraints | 0.241230 | 0.264083 | +0.022853 |

Held-out exact registered-form retrieval improved from 1/4 to 2/4. This is a small development
diagnostic, not proof of generalization: each task cell has only four rows, the adapter emits
longer held-out answers on average, and three transfer tasks regressed. The correct conclusion is
that the pipeline and artifact are reproducible and the adapter shows a mixed, retrieval-heavy
signal worth testing on a larger independently designed benchmark. It does not establish that the
adapter is generally better, and it is not Ainglish governance evidence.

Frozen receipts: `training-receipt.json`, `evaluation-base.json`, `evaluation-adapter.json`,
`evaluation-comparison.json`, and `adapter-artifact-receipt.json`.
