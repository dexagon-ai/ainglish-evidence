# Result

All 264 planned observations completed with no download and no inference retry. Raw response SHA-256:
`12f2e21c2c2838cb537ac1f1b7302f66489df6b969d11cf4ddde92d161198e89`.

## Ainglish-arm outcomes

Counts are successes out of the complete item stratum. Zero-repair success is the immediate action;
final success permits the one frozen clarification when the first decision was `clarify`.

| Exposure class | Prompt track | Base zero | Adapter zero | Base final | Adapter final |
|---|---|---:|---:|---:|---:|
| trained surface | cold | 5/14 | 3/14 | 11/14 | 12/14 |
| trained surface | one exposure | 8/14 | 4/14 | 10/14 | 13/14 |
| withheld surface | cold | 2/8 | 1/8 | 6/8 | 6/8 |
| withheld surface | one exposure | 4/8 | 2/8 | 6/8 | 6/8 |

The adapter did **not** improve immediate Ainglish task execution. On trained surfaces its paired
adapter-minus-base zero-repair difference was -2/14 cold and -4/14 after the one-use reference. It
improved final success by +1/14 and +3/14 respectively, only after substantially more clarification.
On exact-marker holdouts, final Ainglish success was unchanged and zero-repair success fell.

## Broad behaviour change, not selective Ainglish uptake

Across all 132 cells per condition, the base produced 47 immediate actions, 58 clarifications, and
27 invalid first responses. The adapter produced 22 actions, 97 clarifications, and 13 invalid first
responses. Each condition then produced the same 12 malformed repair responses at the same frozen
cell locations.

The final-success gains were not Ainglish-specific. On trained surfaces the adapter also changed
careful English from 9/14 to 10/14 final and bare English from 11/14 to 13/14 final. On withheld
surfaces it changed careful English from 5/8 to 6/8 and bare English from 3/8 to 6/8, while Ainglish
stayed 6/8. The most defensible reading is a broad shift from invalid or immediate output toward
clarification-and-repair, not demonstrated learning of the trained Ainglish surfaces.

## Interaction cost

The frozen scorer cannot include token usage from a non-action repair, so its standard token
contrasts are marked invalid in `analysis.json`. The recovery block reports complete raw interaction
totals including those calls. The adapter's mean raw interaction-token count was higher than the
base in every one of the 12 track/arm/exposure groups. No present-efficiency claim is supported.

That result does not contradict the project's future-training rationale: this was one tiny
development LoRA trained on 76 rows, not incorporation into a foundation model's pretraining data or
tokenizer. It does show why exposure claims must be tested at the actual task outcome, with current
costs reported honestly, rather than inferred from form retrieval.

## Analysis recovery

The frozen raw run is unchanged. `analyse.py` refused because the runner represented 24 malformed
repair continuations as explicit `invalid` objects while the older benchmark scorer accepts only an
action or `null`. [`ANALYSIS_ERRATUM.md`](ANALYSIS_ERRATUM.md) documents the mechanical scoring view;
`analyse_recovered.py` maps only those already-unsuccessful repair objects to missing repairs and
keeps complete raw token totals separately. The recovered analysis has SHA-256
`9266515f0f3d6b3a98794de308619a98337282b834d60146e5a8968d474058cd` and content seal
`57effdae884f7845bc96160a7b256a1d05b16073e4323118cf274ee9760cb2fd`.

This remains project-linked development research, not independent governance evidence, human
validation, proof of external adoption, or a model-family result.
