# `some-or-all / some-but-not-all` comprehension packet

This packet advances the Ainglish proposal:

`some-or-all-some-but-not-all-does-some-leave-room-for-all-2`

It freezes answer-bearing inputs before any reader call. `freeze-receipt.json`
must continue to say `reader_calls: 0` until an attempt has been minted against
the exact clean-run manifest.

## Claim boundary

The proposal forbids pooling the two forms. The packet therefore contains two
separate claim carriers, each with 100 real items and 16 construct-free planted-
effect calibration items:

- `some_or_all-careful-items.json`
- `some_but_not_all-careful-items.json`

Each marked form is compared only with its complete careful-English mapping.
The primary answer is exact joint recovery of two consequences: whether a zero-
member matching group is possible and whether the full named set is possible.
The questions and answers use boundary vocabulary absent from both messages.
Question polarity and answer position are balanced, and the same 100 frames
occur under both forms across ten domains.

Bare `some` is not a valid English arm for protocol-v2 claim confirmation. Its
ambiguity is retained in two separately frozen descriptive diagnostics:

- `some_or_all-bare-items.json`
- `some_but_not_all-bare-items.json`

These files may quantify marked-versus-bare behavior, but no result from them
can replace non-inferiority to complete careful English.

Population-coverage confusion, epistemic/exact-count over-reading, invalid-set
handling, and corruption tolerance remain separate diagnostics. They do not
enter the claim-carrier scalar and must not be represented as having been run
by this freeze.

## Gates before reader spend

1. Rebuild with `python3 build_packet.py` and require a clean diff.
2. Check every digest and structural invariant in `freeze-receipt.json`.
3. Commit and publish the answer-bearing packet; pin each run spec to an
   immutable raw-GitHub commit and the item-array digest.
4. Run the served panel harness with `--dry-run`; this uses a mock oracle and
   spends no reader calls.
5. Mint the matching attempt before the first real reader cell. Preserve and
   file null, adverse, and supportive outcomes alike. Abort only for a frozen
   input, calibration, yield, transport, manifest, or declared GPU-contract
   failure.
6. Report the two forms separately. A result on one form cannot rescue the
   other.

An independent replicator should author fresh frames without opening these
answer-bearing files, use a different reader instrument, mint independently,
and disclose any overlap that would collapse settlement independence.
