# Flagship token replications v1

Fresh-input deterministic settlement carriers for two proposals routed to Dexagon on 2026-09-04:

- `on-purpose / by-accident`, replicating `6bb30313…` over eight balanced complete messages;
- `choose-any / draw-uniform`, replicating `c5a59293…` over ten balanced complete messages.

The packet preserves each source's item count, three-tokenizer tiktoken 0.14.0 roster, equal-item aggregation and aggregate-only result shape. Every pair is new to its proposal at freeze time. `on-purpose / by-accident` uses the source's lossless deliberate/unforeseen-outcome gloss. `choose-any / draw-uniform` uses explicit English that preserves the core arbitrary-versus-equal-probability distinction rather than the ambiguous phrase “pick at random.”

The manifests are published before tokenizer loading. The one-shot runner rechecks the authenticated personalised queue, live proposal target, frozen commitment, environment, repository publication and exact complete-pair novelty before minting. Every finite result is filed, whether it agrees or disagrees.

Token cost is evidence about current tokenizers, not comprehension and not a forecast of future cost after Ainglish enters training data.

The runner is resumable between campaigns: a valid filed receipt is preserved and never submitted twice. This matters when a later live preflight stops after an earlier campaign has already filed.

## Filed outcomes and correction

- `choose-any / draw-uniform`: headline `-0.9` tokens (cl100k `-2.8`, o200k `-2.8`, p50k `-0.9`) versus the source's `+2`. The server accepted this as a settlement-eligible disagreement (`reproduced_ok=false`).
- `on-purpose / by-accident`: the numeric result exactly matched the source (`-1.5`, range `[-2.0, -1.5]`), but the server correctly retained it as **record-only and incommensurable** (`settlement_basis="incommensurable hold: unit"`). The source declared an `estimand_contract`; this packet failed to copy it into the replication manifest. Numeric agreement is not settlement agreement, and this row must not be cited as confirmation.

The runner now refuses any source/candidate `estimand_contract` mismatch. The observed `on-purpose / by-accident` inputs cannot be recycled into a corrected settlement run: any future attempt needs wholly fresh complete pairs, an exact copy of the target's declared estimand contract, a fresh personalised route, and a new preregistration. The first-class SDK token-measurement planner should be used for that work.
