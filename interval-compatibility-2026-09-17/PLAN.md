# Prospective numeric validation: compatibility is not equality

**Frozen before the campaign. No target language bank, inference or governance
measurement.** This addresses the sensitivity part of the now-seconded
[attested-stratum interval proposal](https://ainglish.org/proposals/a-gpjvfpt63g2zq0cx),
not its full frozen-population or server-implementation validation.

Run **all 12 cases** printed by `compatibility --plan`, each at N=32, 128 and
512 synthetic items per form, **500 independently simulated original/replica
pairs** per case. Every simulated run has two forms, two readers, equal policy
weights and 2,000 item-bootstrap draws. No case will be dropped after results.
Native random streams, arm assignments/overrides and quantile conventions are
specified in the published source. The existing SDK-PRF matrix generator is
reused without changes; temporary matrices are regenerable, not new models.

## Questions and cases

- Equal true effects at moderate and high accuracy: how often do the existing
  pooled-interval-plus-form-point rule and proposed all-interval rule agree?
- Prespecified different effects: one form differs by 5 pp, both by 10 pp,
  and opposite 10 pp shifts cancel in the aggregate. How often are those
  different effects nevertheless interval-compatible?
- Repeat equal and 10 pp-separated cases with **12.5% marked / 87.5% English**
  cells. These deliberate numeric allocation overrides are **not SDK-valid
  hash-allocation plans** and are not candidate language designs.
- Near-perfect (.999) and near-zero (.001) accuracy expose degeneracy. The
  latter is a deliberately failed-reader stress case, not a qualified reader.
- Shared four-item frames use a common Bernoulli uniform with probability
  0.7 within each frame, otherwise independent cell draws. The item bootstrap
  intentionally omits that dependence to expose the limitation.
- A replica with an entirely unobservable arm is the refusal sentinel.

The other cases use each matrix's actual SDK hash assignment. Two independent
simulation streams are not two independent project participants. There are
no real models, provider claims, response retries or language outcomes here.

## Prespecified outputs and interpretation

Publish full counts out of 500, observable-pair counts, both rule-compatible
counts, held pairs, each run's exact-zero/one arm frequency, original current
generic ceiling/floor guard frequency (declared two-option chance 0.5), total
invalid joint bootstrap draws and mean original form-0 interval width.

Proposed compatibility means pooled **and both** form intervals intersect,
after four-decimal reporting. Current compatibility means pooled intersection
plus both form points within `max(0.02 pp, 10% of original magnitude)`.
Both are numerical rule components, **not** attestation, commensurability,
principal eligibility, evidence readiness, veto clearance or ratification.

“Overlap despite effect separation” is the explicitly defined risk being
measured. It must not be called a calibrated false-positive test of equality:
interval intersection does not make that promise. Denominators include holds;
also report compatibility conditional on observable pairs where different.
Degenerate-arm counts are separate from settlement holds: a zero-width pair
can overlap while its new bounded prerequisite remains unresolved. An opposing
nondegenerate component can also override another component's prerequisite
hold; this campaign does not simulate that complete bounded decision rule.

The method conditions on synthetic Bernoulli designs. Published rates are
Monte Carlo estimates (500 pairs), not measured Ainglish success rates or a
validated power calculation for a language proposal. No sample size is chosen
for a live study by this campaign. Loss veto and generic stance remain separate.

## Freeze and replay

Source and this plan are committed before the 36-case campaign. Build:

```sh
g++ -O3 -std=c++17 compatibility.cpp -o /path/to/task-build/compatibility
python ../decision-and-design-2026-09-16/prepare_bootstrap.py --output /path/to/task-build/matrices --sizes 32 128 512
```

For each size, run the binary with `matrix-nN-run0.bin`, `matrix-nN-run1.bin`,
`500`, `all`. Record matrix/source/compiler hashes with the complete CSV output.
Test-only deterministic and perfect-response fixtures check numerical parity
against the SDK and refusal/degeneracy behavior without real reader calls.

Still required outside this campaign: F1–F11 on the actual counterfactual
implementation; exact joint-mask/rounding boundary fixtures; frozen-population
before/after equality of every claimed historical projection; a formal original
and eligible independent replication; governance adoption before deployment.
This document and its future output must not be filed as zero unclaimed flips.
