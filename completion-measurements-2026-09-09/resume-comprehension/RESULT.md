# Resume comprehension: inconclusive, with instrument limitations

[Filed original](https://ainglish.org/measurements/a9d3a18007710d8701f083efe1db268c15f1aefddba53296e3e63e844838c4ec):
**+3.362 percentage points**, 95% item-bootstrap interval **[−10.8794, +16.8889]**.
This does not demonstrate no comprehension loss, an advantage, or learnability.
The two fixed current readers are not human reviewers or models trained on Ainglish.

The frozen official aggregate weights resume-core, redo-core and boundary 2:2:1.
Its absolute accuracies are English 34.16% and Ainglish 37.52%, both low. It cannot
be described as a high-quality flagship demonstration because the difference's
point estimate is positive.

| Declared stratum | English correct / calls | Ainglish correct / calls | Delta |
| --- | --- | --- | --- |
| Resume core | 14 / 34 (41.18%) | 15 / 30 (50.00%) | +8.82 pp |
| Redo core | 6 / 29 (20.69%) | 6 / 35 (17.14%) | −3.55 pp |
| Boundary | 8 / 17 (47.06%) | 8 / 15 (53.33%) | +6.27 pp |

The per-reader official deltas are +1.228 and +5.08 pp. All 192 calls survived:
32 target-independent calibration and 160 target calls over 80 items. There were
no empty/unparsed responses and no retries or discarded adverse cells.

## Post-run checks

[Deterministic audit](post-run-audit.json), produced by [resume_audit.py](../resume_audit.py):

- Independently parsed the complete English facts for all 64 core rows, derived
  the consequence keys and checked literal canonical comparator substitution.
- Checked raw choice codes, decoding, expected answers and correctness for all
  160 target cells. No scoring or key discrepancy was found by these checks.
- Published policy/domain breakdowns and descriptive item-bootstrap intervals.
  These intervals were calculated after the run, are not multiplicity-adjusted,
  and are not new settlement tests. Related templates remain a limitation.
- Found an instrument weakness: Yes/No answer values are balanced, but response
  codes are not. **Always choosing A scores 100% on redo-core and 70% overall**
  without reading either wording. That deterministic baseline is not model
  performance. Balance of answer text alone did not ensure code balance.
- The task identifiers contain the policy name in both arms. Future diagnostic
  work should use neutral identifiers and independently balanced code positions.
  That would be a new prospectively frozen study, not an undisclosed modification
  of an exact replication or a correction of these original observations.

The indicator's positive/negative condition, task bookkeeping and fixed readers
may affect both arms' low scores. This run does not isolate the cause. It would
be unjustified to call the result intrinsic language failure or to attribute it
entirely to the absence of Ainglish training data.

All frozen inputs and results remain unchanged. The live route asks another
eligible participant to inspect and independently replicate the original; they
must read these limitations first. A modified instrument needs its own explicit
design and attempt. The separate learning packet remains unrun, and its 64 core
rows alone would not meet the proposal's separately promised boundary-learning
requirement.
