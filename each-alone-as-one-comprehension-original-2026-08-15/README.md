# `each-alone / as-one` comprehension original

Status: **attempted once; refused at the preregistered calibration gate before any scientific
cell; no measurement emitted and no rerun performed**.

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

`runspec-dedicated-gpu0.json` pins `items.json` to immutable freeze commit
`7e28ac7032ea9bad9123126d3a09a6f8909c482c`. Its exact on-disk SHA-256 is
`51e49b1a50d3d3f3e68519797d69d11f3080cb6a9c38ac23b2cfc0ccf62a69db`.
The Ainglish 0.2.29 dry run passed item retrieval and digest verification, calibration-first
execution, arm balance, yield, bootstrap, resample-down, attempt-manifest preview and payload
construction with zero API and zero model calls. `dry-run.txt` is that exact transcript; its
SHA-256 is `a46a6ead0e3aa1a1b967c0fac732647b7e73120f2861bb914f22e3bdcbe4a911`.

## Single-attempt outcome

The pre-reader design above was committed and pushed at
`f40940d51c2ff8ae2fdbb4dea55578310a28df4b`. On 2026-08-15, the shared Ollama service had no
loaded model and host GPU 0 (`00000000:24:00.0`, RTX 3090) had 24,308 MiB free immediately before
minting. A disposable loopback-only Ollama service discovered that physical device as CUDA 8.6;
the two readers ran there sequentially with no CPU fallback.

Ainglish attempt `c4ddce0b-eac5-46b4-b1ec-b391e62516cc` was minted before the first reader call.
Its manifest commitment is
`1b310c29e62fe9440f056a60fc0dff5f82cf990e9435afe79216de1eae652455`.

The harness then refused at calibration:

- all 24 planned calibration cells were attempted;
- the explicit-count arm scored 7/12 (`0.583333...`), while the ambiguous arm scored 6/12
  (`0.5`);
- the observed positive-control gap was therefore only 1/12 (`0.083333...`), below the frozen
  `0.5` minimum;
- zero real cells were attempted, no measurement was emitted, and the server records the attempt
  as `aborted` with no successor.

This is evidence that this reader/control combination did not pass its competence check. It is
**not** evidence for or against `each-alone / as-one`. In accordance with the one-attempt design,
the controls were not altered after seeing the result and the experiment was not rerun.

The exact receipts are:

- `runspec-dedicated-gpu0.json.attempt-c4ddce0b-eac5-46b4-b1ec-b391e62516cc.abort.json` — canonical
  receipt SHA-256 `2334a5a7f09cf9dc5608bda052ceaabb801c721ddb62be52a39fc2523cf431f2`
  (the server's committed `preflight_receipt_hash`); on-disk SHA-256 including its trailing newline
  `3ecc0673273b30dd486586bf6a78f8a0af759a28236ce64cdc8d1e41230147cd`;
- `runspec-dedicated-gpu0.json.attempt-c4ddce0b-eac5-46b4-b1ec-b391e62516cc.cells.json` — canonical
  receipt SHA-256 `ab823fb22a3d27ad4bd1bfef0ca9874baf45174583f4a87068e4555ec98267b9`;
  it explicitly contains zero real rows (on-disk SHA-256 including its trailing newline
  `8cfb443276a404c68460cd9d8eb2680234233edb7718fe4378290162c7e4d190`).
