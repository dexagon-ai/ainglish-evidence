# Public UVF census kit v1

This zero-secret, standard-library Python kit lets any reader verify the seven
`unclaimed_verdict_flips` originals' public proposal and measurement inputs,
then traverse the complete public proposal and measurement verdict surfaces
twice. It preserves the server's measurement cursor chain, records the live
deployment identity, and emits a machine-readable receipt.

It deliberately does **not** claim to be a settlement-eligible independent
replication. The originals' causal gate includes focused tests and exact source
boundaries in the private `ai-nglish/ainglish-symfony` repository. An outsider
cannot execute that gate from public material. A stable public census is useful
corroboration, but relabelling it as equivalent evidence would weaken the
protocol. No private source is copied into this repository.

## Run

Python 3.10 or newer is sufficient; no SDK, account, API key, model or GPU is
required.

```bash
python3 verify_public_surface.py --selftest
python3 verify_public_surface.py --out public-surface-receipt.json
sha256sum -c CONTENT.sha256
```

Run the checksum command from this directory before execution. `CONTENT.sha256`
addresses the immutable fixture, runner and explanation. The generated receipt
is intentionally excluded because its timestamp and current live projection
change on each run.

## What the receipt establishes

- Each frozen target still resolves as an active, valid original for
  `unclaimed_verdict_flips`.
- Its stored manifest and implementation/deployment pins remain publicly
  inspectable.
- Every currently served proposal and measurement verdict surface was included
  in two complete traversals.
- The two traversals either agreed exactly or the run fails visibly.

It does not establish that a private focused test passed, that a private diff
has the declared source boundary, or that no historical flip occurred between
the original pre-deploy snapshot and this run. An independent principal with
repository access should instead use
`../protocol-uvf-batch-v1-2026-09-03/independent_replication.py`, which keeps
those additional gates and can file settlement evidence.
