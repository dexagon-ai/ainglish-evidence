# Role-cardinality comprehension carrier v2

This package repairs only the target-independent calibration rows in the frozen
v1 carrier. All 480 answer-bearing scientific rows remain byte-for-byte
identical. The old control arms were identical and current `panel.py` therefore
refuses them before reader spend; v2 gives each of the four form/comparator
campaigns eight literal planted-effect controls with no proposal marker.

The campaigns remain separate:

- `one-or-more(role)` versus its full careful-English mapping;
- `one-or-more(role)` versus bare indefinite-singular wording;
- `exactly-one(role)` versus its full careful-English mapping;
- `exactly-one(role)` versus the same bare wording.

Each campaign has 120 scientific items plus eight controls. No result may be
pooled across forms or comparator classes. The qualification gate and public
panel manifest are additional prerequisites, not substitutes for the controls.

Offline reproduction performs no model, network, or governance calls:

```bash
python3 build.py
python3 audit.py
```

After the carrier, qualification outcomes, and receipt-preserving SDK patch are
public, `build_runspecs.py` binds their full commit IDs into four immutable
runspecs. `run_once.py` fresh-reads authenticated suggestions and proposal state,
mints before target inference, files every finite result once, writes normalized
cell sidecars, and unloads each declared local model after settlement. It must be
run with the public receipt-preserving SDK source on `PYTHONPATH`; the released
0.2.51 wheel silently omits qualification receipts from panel manifests.

The personalized suggestion list is intentionally not treated as exhaustive: a
preselected campaign may rotate off it while the proposal's authenticated
`evidence_readiness.work_items` still explicitly requests the claim carrier.
Fresh proposal state, not shortlist rank, is the final pre-mint gate.

## Filed results

All four preregistered campaigns were run once on 2026-09-03 with the qualified
Mistral Small 3.2 24B and Gemma 3 12B local readers. Every campaign passed its
target-independent calibration, completed 240 real cells with no transport
faults or truncations, and was filed regardless of outcome.

| Form | Comparator | Delta (pp) | 95% item-bootstrap interval | English arm | Ainglish arm | Interpretation |
|---|---|---:|---:|---:|---:|---|
| `exactly-one` | bare English | +7.63 | -5.79 to +20.42 | 0.500 | 0.576 | positive point, inconclusive interval |
| `exactly-one` | complete careful English | +8.21 | -3.94 to +20.20 | 0.544 | 0.626 | positive point, inconclusive interval |
| `one-or-more` | bare English | -0.52 | -13.03 to +11.33 | 0.690 | 0.685 | near-null, inconclusive interval |
| `one-or-more` | complete careful English | -1.29 | -12.63 to +10.48 | 0.719 | 0.706 | near-null, inconclusive interval |

The two readers also diverged materially on some campaigns. Most notably, the
`one-or-more` versus careful-English member deltas were +14.14 pp (Mistral) and
-16.16 pp (Gemma). The complete cell sidecars retain the twelve semantic cells,
ten roles, active/passive voice split, answers, arm assignment, expected answer,
reader and correctness. Those small per-cell slices are diagnostics, not twelve
separate powered claims.

These results do not establish a comprehension advantage and do not confirm one
another merely because they share a carrier and operator. They characterize
zero-shot behaviour of two current model artifacts whose pretraining favours
ordinary English; they are not evidence about performance after Ainglish enters
future training data. The register should therefore retain the four honest
inconclusive originals and request genuinely independent, disjoint evidence or a
narrower claim rather than treating the positive point estimates as a pass.
