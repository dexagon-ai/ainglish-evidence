# Bounded completion and publication

This finisher waits at most24 hours for the already-running exact CPU continuation.
It does not run a model, resume an interrupted call, change a threshold, kill a
process, change a service, or create governance evidence.

On normal completion it verifies the journal, original request model/options,
full reference membership, reference scoring and gate, and any sender/receiver
readbacks. It publishes all planned context/arm slices and missing/false counts.
On process exit without a final result it retains the partial raw journal and
uncertain-call IDs without selecting a partial accuracy headline or inferring a
stopping cause.

Publication uses one dedicated checkout of the user's own public evidence repo,
copies only an explicit list of this study's generated result/journal files,
and performs a fast-forward-only push. It does not stage unrelated work, change
history, open a PR, or stage a language release. A concurrent remote update or
resource-reserve failure leaves recoverable local artifacts for inspection.
