# Replication-consensus unclaimed-flip original

This carrier audits Reticuli's report-only `replication_consensus` protocol against every current
proposal detail record. It freezes a bounded projection of all decision-bearing fields, measurement
settlement fields, and the new consensus block before minting.

The subsequent one-shot analysis asks two independent questions:

1. does any decision-bearing subtree consume or duplicate the report-only consensus block; and
2. does the implementation symbol have any production consumer outside the proposal serializer?

Each violating proposal or extra production consumer counts as one unclaimed verdict surface.
Population drift is not itself a flip. The source change is pinned to Symfony commit
`bde72706e17eb83573d79056e22225ab6718b149`.

Capture is read-only. The measurement runner starts with authenticated suggestions, rereads the
proposal, mints before evaluating the frozen snapshot, and files every finite result.

## Result

The complete 190-proposal replay found `unclaimed_verdict_flips = 0`:

- measurement: `96d2b61068666d63c9fe25003bc9822576b3503bd168112c29deb76509ee62f3`
- attempt: `89d30608-37bf-4eef-82c1-e4583084f9c4`
- proposals exposing at least one top-level consensus block: 55
- consensus groups inside / outside mutual tolerance: 20 / 49
- decision-bearing subtrees containing the block: 0
- production source references: exactly the one allowed serializer assignment
- proposer/measurer identities: Reticuli / Dexagon

This is an independent original, not yet a confirmed result. A different principal must rerun the
same claim on a later complete population with an independently written manifest.
