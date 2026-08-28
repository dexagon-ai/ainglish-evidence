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
