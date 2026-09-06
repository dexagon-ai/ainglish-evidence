# Controlled usefulness follow-up: gains, limits and failed guards

The new Ainglish-trained adapter improves cold Ainglish reading over matched
English training on this authored transfer set: **226/252 (89.68%) versus
198/252 (78.57%), +11.11 percentage points**. The 42-frame cluster-bootstrap
interval is [2.38, 20.24] pp. But the predeclared combined criterion **fails**:
the instruction-update family loses 6.25 pp, below its -5 pp guard. Do not call
the pilot an all-family success or use the pooled gain to waive that failure.

English retention for A-trained improves overall versus base, 221/252 versus
190/252 (+12.30 pp). The English alternatives family nevertheless falls from
35/48 to 31/48 (-8.33 pp). This remains visible even though the English retention
guard was declared at the overall level. These are point guards, not a proof of
noninferiority. Frame-bootstrap intervals condition on the authored grammar and
fixed reader; they do not establish effects across arbitrary model populations.

## What ran

5,808 calls: 5,748 target cells plus 60 target-independent format controls, all
retained. All controls were correct; every target was a valid untruncated option.
No target retries, new model downloads or governance-evidence writes. One cached
NF4 Qwen2.5-7B-Instruct base, two newly trained small LoRA adapters, and two
previously trained adapters. Exact base/tokenizer/adapter pins and all raw
responses are retained. The old adapters were tested only for retention and
answer-permutation diagnostics; their older results were not changed or replaced.

Both new curricula contain 168 distinct paired cases, two epochs, 42 steps,
balanced answers (56 each A/B/C). They use the same case grammars and new domain
words, with no exact train/evaluation repeats. The 252 retention cases have
balanced labels (84 each); they represent 42 grammar frames, **not unseen semantic
families**. Input tokens per training epoch differ: 17,614 Ainglish versus 18,442
English; supervised tokens are 504 each. This is matched examples/hyperparameters,
not equal compute. Evaluation targets used 683,524 input and 11,496 output tokens.
Fixed-tokenizer segmentation did not change during adapter training.

## Every retention family

Cells below are correct Ainglish / correct English within the named family.

| Family | Cases per arm | Base | A-trained | E-trained | A-trained minus E-trained, A arm |
| --- | ---: | ---: | ---: | ---: | ---: |
| Alternatives | 48 | 34 / 35 | 43 / 31 | 37 / 43 | +12.50 pp |
| Deadline | 48 | 35 / 35 | 42 / 42 | 40 / 43 | +4.17 pp |
| Multiplicity | 30 | 23 / 24 | 26 / 26 | 25 / 27 | +3.33 pp |
| Participants | 30 | 27 / 27 | 30 / 30 | 26 / 26 | +13.33 pp |
| Fact / choice | 48 | 16 / 27 | 42 / 48 | 24 / 44 | +37.50 pp |
| Instruction updates | 48 | 42 / 42 | 43 / 44 | 46 / 48 | **-6.25 pp** |

The primary 252-case comparison contains 37 gains, nine losses and 206 unchanged
correctness outcomes. The previous A/E adapters score 205/252 and 204/252 on the
new A arm, respectively; this does not rescue their earlier failed pilot.

## Drafting, wording, workflows and composition

| Test and arm | Base | A-trained | E-trained |
| --- | ---: | ---: | ---: |
| Faithful Ainglish draft selection, /72 | 56 | 61 | 58 |
| Faithful English draft selection, /72 | 67 | 69 | 70 |
| Exact Ainglish wording, cold /72 | 45 | 55 | 52 |
| Exact Ainglish wording, reference /72 | 58 | 60 | 55 |
| Careful English wording, cold /72 | 59 | 64 | 58 |
| Careful English wording, reference /72 | 69 | 70 | 69 |
| Hyphens-to-spaces, cold /72 | 51 | 50 | 51 |
| Hyphens-to-spaces, reference /72 | 54 | 51 | 54 |
| Arbitrary labels, cold /72 | 36 | 31 | 36 |
| Arbitrary labels, reference /72 | 51 | 47 | 52 |
| Ainglish workflow checkpoints, /96 | 56 | 69 | 62 |
| English workflow checkpoints, /96 | 65 | 73 | 74 |
| Ainglish joint composition answers, /72 | 22 | 27 | 22 |
| English joint composition answers, /72 | 25 | 20 | 22 |

Draft selection is constrained choice among faithful, wrong-pole and underspecified
messages. It is **not free-form writing**, real uptake or recipient clarification.
English wins that comparison in all three new conditions.

The wording factorial holds the information-bearing distinction constant. The
arbitrary-label cold condition is deliberately unfamiliar, not a fair substitute
for ordinary careful English. Reference guides add an average 48.17 native input
tokens for English, 52.17 for Ainglish, 51.50 for spaces and 50.83 for labels.
Their costs and separate arm changes matter. Hyphen-to-space is a zero-change
condition for `supersedes` / `supplements`; those rows are retained, not counted as
new independent surface evidence. Twelve participant option-permutations change
no decoded answer for base or A-trained, and one correct answer becomes incorrect
for E-trained. They are diagnostics of the same cases, not twelve new observations.

Workflow comprises 32 three-checkpoint episodes with only eight structural
patterns. It distinguishes obligations, in-flight work and completed effects;
there were no real actions. Intervals cluster by episode. Composition covers
48 participant/deadline and 24 multiplicity/alternative cases with four joint
answers, not arbitrary nesting. Accuracy is low in both languages; the largest
Ainglish score is only 37.5%. This does not support deployment-grade composition.
All per-family/arm scores, decoded answer counts, constant-label and literal
semantic-answer-text baselines, native costs, discordant IDs and paired intervals
are in `RESEARCH-RESULTS.json`. A literal-answer baseline does not exhaust all
possible semantic shortcut policies; balanced letters do not prove task validity.

## Consequences

1. Retain the specific evidence that training can improve some familiar Ainglish
   distinctions, particularly fact/choice. Do not extrapolate to all constructs,
   humans, arbitrary readers, new semantic tasks or tokenizer reform.
2. Prioritise update-family repair/teaching and English-alternatives retention
   before another claimed successful training pilot. Keep the failed guards fixed.
3. Audit low joint-composition recovery and frame construction before spending
   on a larger benchmark. No favourable subset should replace the frozen result.
4. Offer exact-reference phrasebooks and clear English as current practical
   tools. Real use and future public-domain training distribution are complementary
   next steps, not proof of benefit already achieved.

Inputs were public at `365a6c52d4ed3149ccb8d3c01857eefbc56eef68`; new adapters were
sealed at `44727be` before evaluation. `analyse_research.py` independently checks
frozen digests, expected unique target coverage, raw answer decoding and receipts
before writing the report. Bootstrap draws: 2,000, seed 2026090613. Analysis made
no new model calls. The original pilot's exact 10-gain/10-loss rescore is included.
