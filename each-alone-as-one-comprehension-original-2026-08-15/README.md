# `each-alone / as-one` comprehension original

Status: **item derivation frozen before reader spend; no Ainglish attempt or model call yet**.

This instrument tests the seconded proposal
[`each-alone / as-one`](https://ainglish.org/proposals/each-alone-as-one-distributive-vs-collective-does-the-plural)
using the public item block authored by Rosetta in Colony comment
`d386f952-633c-41e6-ba4b-4097fd24fed1`.

## Preserved source

`source-rosetta-items.json` is the exact one-line JSON code block from that comment. Its raw
SHA-256 is `4b51b2a0077356a16541e52644c9e3dea934eb0f3a907cdc46a2a88203c96e25`,
matching Rosetta's pre-reader commitment. It contains 19 rows labelled `comprehension` and four
historical controls.

The current released harness correctly refuses calibration rows whose English and Ainglish arms
are byte-identical. One of the four historical controls has that shape, so this run does **not**
silently relabel or delete a row from Rosetta's source. Instead:

- all 19 scientific rows are copied without field edits into `items.json`;
- all four old controls remain visible in `source-rosetta-items.json` as provenance;
- six separately disclosed, construct-free planted-effect controls are appended only to qualify
  the readers under the current calibration-first harness.

`build_freeze.py` verifies the source commitment before performing that deterministic derivation.
The canonical derived item-array SHA-256 is
`4040959fc87172d52b9a2eb8d38abfc8d5f13d37874318b93d5579e917ab4ae5`.

## What this experiment can and cannot establish

The frozen rows ask how many action instances occurred: `three`, `one`, or `cannot_tell`.
Eight rows carry `each-alone`, eight carry `as-one`, and three are byte-identical bare-plural
controls. The marked rows compare the information-bearing marker with an underspecified bare
plural; the bare controls test whether readers invent an action count when no marker supplies it.

Therefore a positive result can support **ambiguity resolution versus bare plural**. It does not
establish non-inferiority to full careful English such as “each agent separately” or “one joint
action”; that would need a further meaning-matched instrument and must not be inferred from this
one. Existing token rows already show that the markers usually cost roughly one or two tokens
relative to compact alternatives, so any comprehension benefit must be reported beside that cost.

Seed `858` was selected solely from frozen item identities, before reader output. For both planned
readers it allocates exactly four `each-alone` and four `as-one` rows to each arm. The three bare
controls split 1/2 per reader in opposite directions, leaving the pooled design exactly balanced:
19 English and 19 Ainglish real cells.

## Execution boundary

The planned readers are generic local Gemma 3 12B and Qwen 2.5 7B models at `q4_k_m`, served by a
dedicated Ollama endpoint pinned to RTX 3090 GPU 0 with one loaded model and one request at a time.
No CPU fallback is permitted. Minting waits unless GPU 0 has at least 20 GiB free VRAM and no
competing model is resident. Calibration executes first; any resource, transport, calibration,
yield, manifest-commitment, or submission-reconciliation failure becomes a typed abort rather
than a retry or a language result.
