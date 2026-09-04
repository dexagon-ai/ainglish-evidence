# Correction: on-purpose / by-accident is record-only

The 2026-09-04 `on-purpose / by-accident` filing numerically matched target `6bb30313…`, but it is not a settlement replication. The server receipt is authoritative:

- `settlement_eligible: false`
- `reproduced_ok: null`
- `settlement_basis: incommensurable hold: unit`

Cause: the target manifest declared a report-only `estimand_contract` with `unit_span: complete message`; the replication manifest omitted that declaration. The register therefore held the one-sided unit declaration exactly as designed.

No historical bytes are changed or deleted. The filing remains useful record-only evidence of the computed token counts. Any public summary must call it record-only, not confirmed, reproduced, or settlement-bearing.
