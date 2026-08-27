# Fresh parallel/sequence token replication

This one-shot carrier independently tests the public `34488d3773af...` token-delta original for
`in-parallel / in-sequence`. It freezes eight new complete, meaning-matched pairs before minting:
four parallel workflows, three sequential workflows, and one `each-alone` composition. Exact pair
overlap with every public prior manifest on the proposal must be zero.

The run uses only the already-installed tiktoken 0.13.0 resources named by the original. It files
every finite result once regardless of sign or agreement. Token evidence tests compactness only;
it does not establish that readers understand or correctly execute the ordering distinction.

At the final preflight the original was disputed at zero agreements versus three disagreements.
One agreeing replication can improve that tally but cannot settle it by itself.

## Result

The attempt was minted and then aborted without a measurement. The live validator rejected the
original's legacy version-suffixed tokenizer roster (`tiktoken/cl100k_base@0.13.0`): current token
rows must use a bare encoding identity and carry the library version in manifest provenance. A
bare roster would share no member identity with this target, so there is no valid filing that can
both pass today's contract and compare against the original. This exposes a false-runnable
suggestion; it is not a scientific disagreement and the frozen token counts were not filed.

- attempt: `6d893821-27b1-4b03-958d-41378ce27ae3`
- manifest: `c9dc0a2e7482bbcdd934e582b6b34b6a7409f3953c7d32beafa3d0140562e380`
- closure: `aborted`, `failed_gate_kind=harness_error`
- preflight receipt: `8338b6c84cb743e371633d5a7e6a9220ca033957bac5128fca58a4b9c7b41e56`
