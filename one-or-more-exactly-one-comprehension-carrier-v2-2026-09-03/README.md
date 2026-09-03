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
