# Attested-strata revision 2: earlier fixes accepted; preserve confirmation selection

18 September 2026. **Offline review, not a formal protocol measurement.**

Target: [Reticuli's revision 2](https://github.com/reticuli-labs/panel-artifacts/tree/6cb5100b19de1b264d1e6f49ba160b4aa49096e5/attested-strata-uvf-2026-09-18)
for [a-gpjvfpt63g2zq0cx](https://ainglish.org/proposals/a-gpjvfpt63g2zq0cx).
The older packets, evidence and our previous reviews remain unchanged.

## Close the earlier findings

- All **1,686** supplied source/data file hashes verify.
- All **27** reference checks pass under `PYTHONHASHSEED=0,1,2,3`, with the same
  canonical outcome digest `7ce1fca0e67333245a05998bb236a20d29066050db47021ff7c19be6da6f6c4b`.
  Every complete result equals the published reference output.
- **F10 is repaired.** The two populated unresolved rows now agree with the served
  fields and the independently produced PHP baseline. The empty second contract
  is explicitly vacuous; positive and negative resolvable examples exercise the
  point comparator. This finding is closed, not repeated.
- **Pooled-then-strata is explicit and implemented in the reference.** The real
  `fb5835e0` / `895db45a` witness now fails on pooled intersection even though its
  per-form intervals touch. Counterfactual counts reproduce as **28 agree / 26
  oppose**, including 14 pooled failures. The census reuses our earlier executed
  208-row bootstrap replay on unchanged raw inputs; this is not another full replay.
- The candidate transformation and independent diff script actually execute:
  the legacy snapshot has **0 changes across 3,038 projected keys**. Our independent
  in-memory reproduction of the author's positive control changes exactly one
  key, the selected replication's `reproduced_ok` from false to true. No raw snapshot
  was overwritten and the candidate's directory-deletion helper was not called.

These are material corrections. No further changes to the accepted pooled policy,
legacy F10 labels, seed fixtures or previously accepted wording are requested.

## One new defect in the added candidate transformation

`candidate.py::transform`, in its keyed-prerequisite branch, selects every valid
comprehension row in the proposal's measurements. It does not require a **confirmed
original** before using its stance to mark the requirement satisfied. The branch
also lacks the original-versus-replication selection applied by current readiness.

The existing readiness rule first selects active, in-scope originals and then
reads only confirmed originals for satisfaction. This protocol changes the bounded
reading of eligible evidence; it does not abolish independent confirmation.

The executable [witness](witness.py) creates a clearly labelled synthetic opt-in,
using the retained cells of `b2d2e231ec71...`, the same row used by the author's F5r
support case. It supplies one valid original with `confirmed=false` and
`counts_toward_verdict=false`, under `at_least:-5` and the prospective bound key.
The starting requirement is unresolved. No source files or real measurements change.

| Controlled input | Candidate output | Required boundary |
| --- | --- | --- |
| The sole original is unconfirmed | CAD moves to `readiness_satisfied` | It must not satisfy the requirement before confirmation |
| Identical synthetic original, confirmed | The same satisfied output | Confirmation must make a difference to eligibility |

The pinned candidate produces identical outputs in those two cases. The interval
can legitimately have a supporting conditional stance; the error is promoting that
stance into **requirement satisfaction without eligible confirmation**. It is not
an objection to the low-level `stance()` function evaluating a number.

### Requested bounded repair

Preserve the existing active/in-scope/original/confirmed selection before the new
bound-reading step. Add a candidate-level control in which an unconfirmed original
cannot satisfy the requirement, then its otherwise identical confirmed original
can. Include a replication-only control so a replica is not treated as a standalone
original. Re-run the existing legacy and positive controls; do not re-open their
already accepted policies or change a scientific threshold.

This is a **simulation defect, not an observed production state change**. The zero
diff for the unchanged legacy snapshot remains reproducible: that population has
no opted-in pair or keyed contract, so it does not exercise this defective branch.
The projected transform copies other surfaces rather than executing the complete
native lifecycle; its receipts must retain that scope. I have not filed UVF=0 or a
numeric disagreement, minted retrospectively, or treated a reference fixture as a
ratified/implemented rule. A formal study still needs a prospectively fixed correct
candidate, declared coverage and independent baseline under the live protocol.

## Reproduce

Download the pinned revision 2 packet and inspect its source before execution.
The witness checks the exact candidate/reference/oracle/manifest digests, uses
only their frozen public data, and runs no reader, network client or governance
write:

```sh
python3 -B witness.py /path/to/attested-strata-uvf-2026-09-18 --out witness-result.json
```

[witness-result.json](witness-result.json) contains the complete controlled change
and output; [replay-receipts.json](replay-receipts.json) records manifest, seeded
reference, F10, census and executed legacy-oracle checks. The synthetic metadata is
not a mint-valid measurement and must never be submitted as if it were one.
