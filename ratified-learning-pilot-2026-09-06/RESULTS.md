# Result: no selective Ainglish-training benefit established

Both trained adapters answered **77/96** cold Ainglish tasks correctly; the untouched base answered
**72/96**. Reporting only the improvement over the base would hide that matched English training
achieved the same aggregate gain. All 1,152 target responses and 36 controls completed without a
retry or model download. Every response satisfied the frozen one-letter output format.

## Complete primary comparison

Each cell is correct answers out of the same 96 held-out synthetic cases.

| Weights | Ainglish, no reference | Ainglish + short reference | Careful English, no reference | Careful English + short reference |
| --- | ---: | ---: | ---: | ---: |
| Untouched base | 72 (75.00%) | 75 (78.13%) | 80 (83.33%) | 76 (79.17%) |
| Ainglish-trained | 77 (80.21%) | 83 (86.46%) | 80 (83.33%) | 85 (88.54%) |
| English-trained control | 77 (80.21%) | 83 (86.46%) | 84 (87.50%) | 88 (91.67%) |

The primary Ainglish-trained minus English-trained cold-Ainglish difference is **0 pp**; the
exploratory context-cluster 95% interval is **[-12.5, 12.5] pp**. The corresponding English difference
is **-4.17 pp**. Difference-in-differences is +4.17 pp, interval [-4.17, 14.58], **because English
performance fell**, not because the Ainglish primary improved over its matched control.

The prospective boundary-case non-regression guard failed: 32/36 for Ainglish-trained versus 34/36
for English-trained, **-5.56 pp**, beyond the frozen 5 pp tolerance. Do not sell the difference-in-
differences number as selective learning. Twelve synthetic clusters and one model/seed give weak
population inference; the intervals are explicitly exploratory.

## Distinctions did not all move together

Cold Ainglish, correct out of 16 per construct:

| Distinction | Base | Ainglish-trained | English-trained |
| --- | ---: | ---: | ---: |
| Reader included in “we” | 16 | 10 | 16 |
| Start versus successful-completion deadline | 12 | 14 | 15 |
| Missing fact versus missing decision | 6 | 14 | 8 |
| Independent versus collective act | 12 | 12 | 12 |
| Either/both versus exactly one | 12 | 11 | 10 |
| Replace versus add an instruction | 14 | 16 | 16 |

There is a useful exploratory signal for missing facts versus missing decisions, but it is accompanied
by deterioration on participant inclusion. An overall “trained is better” headline would conceal that
trade-off. The matched English adapter also improves operational use of several Ainglish forms without
being trained on their markers. Task learning, semantic similarity and interference all remain possible;
this small study cannot assign a unique mechanism.

References help some cells and hurt others. In the untouched base, adding the English reference reduced
the overall score from 80 to 76. A definition in context is an exposure condition, not a guaranteed benefit
and not weight training.

## What the cost numbers mean

Both LoRAs used the same cached Qwen2.5-7B-Instruct revision, NF4 loading, seed, 144 matched task answers,
two epochs and 36 optimizer steps. Each had 432 supervised answer tokens per epoch. Complete training
sequences contained 15,825 Ainglish-arm tokens versus 16,464 English-arm tokens per epoch; this is
not equal compute. Training took 243.15 and 243.41 seconds respectively. The two final adapters total
323,094,449 bytes (about 308 MiB); no optimizer checkpoints or model weights were downloaded.

The fixed tokenizer digest is identical in all five model loads:
`c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539`.
Across each 96-case evaluation arm, input costs are 11,194 tokens for cold Ainglish, 16,202 with its
reference, 11,608 for cold English and 16,232 with its reference. Each arm/weight condition emits 192
tokens (letter plus terminator per response). Weight changes altered **none** of the input counts.

These are single reading turns, **not complete real-work interaction costs**. The 414-token cold input
difference does not establish cost per successful task; answers still failed and no clarification or
repair workflow was executed. Training compute itself is not amortized into a claimed operational saving.

## Quality and exposure boundaries

- [Frozen design](PLAN.json) / [checksums](SHA256SUMS.frozen): public commit `8981272`, before training.
- [Adapter receipts](adapter-receipts.json): public commit `d50910e`, before any target evaluation.
- [Pre-evaluation audit](PRE_EVALUATION_AUDIT.md): answer labels are not balanced; majority-label
  baseline is **50%**, not one third. The sixteen cases per family reuse eight semantic patterns twice.
- [Complete machine result](RESULT.json), [raw journals](results), [inference-free rescore](RESCORE.json).
- No independent or human validation, natural-use observation, tokenizer adaptation, external-lab
  training, foundation-model pretraining, or proposal-state change is claimed.
- The reader's original pretraining exposure is unknown; “untouched” means no adapter in this study,
  not proved absence of all Ainglish-related language from pretraining.
- [Train-only supplement](teaching-supplement.zip) remains separate from these now-public test answers.
  A future evaluation must author fresh held-out tasks, not re-label this public packet as unseen.

## What should follow

Keep the matched-English control and the per-construct regression screen. Strengthen the curriculum's
context/boundary diversity, balance answer positions in a new independently specified task set, and test
broader English retention before offering an adapter as generally improved. The already-familiar “we”
distinction should be a retention test, not sacrificed to improve aggregate uptake elsewhere.

In parallel, the [optional real-work pilot](USAGE-PILOT.md) can reveal where explanations or mistakes
actually cost an extra exchange. Do not ask an outside lab to adopt this adapter on a positive performance
claim. A reproducible mixed/null result is instead a concrete question for a suitable post-training
collaborator about curriculum design and transfer. None of this argues that future large-scale exposure
cannot help; it argues for testing the route, not inferring success from publication or lower training loss.
