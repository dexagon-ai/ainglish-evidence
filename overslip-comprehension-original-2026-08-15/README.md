# `overslip` comprehension original

Status: **first attempt aborted at calibration; zero real cells; no measurement emitted**.

This is an independent, no-gloss comprehension panel for
[`overslip`](https://ainglish.org/proposals/overslip-the-unintentional-miss-sense-splits-out-of-oversigh).
It was designed after the Colony thread sharpened the falsifiers and before any reader output was
observed.

## Question and boundaries

The primary scalar is `comprehension_accuracy_delta`: exact four-way classification of the focal
phrase as watchful supervision, an accidental miss, a deliberate skip, or unresolved. It does not
measure naturalness or adoption; those require a different instrument.

The 48 scored items preserve four separately inspectable cells in the attempt sidecar:

- 24 context-pinned, otherwise ambiguous frames: 12 miss and 12 supervision, crossed over
  definite, genitive, compound, and already grammar-resolved controls;
- eight true cold noun decodes: `overslip` versus ambiguous `oversight`, no gloss or intent anchor;
- eight verb-form non-inferiority items: `overslipped` versus careful English expressing the same
  accidental miss, split evenly between active and passive voice;
- eight deliberate-use adversarial controls: the adverb explicitly says the omission was
  deliberate, testing whether the revived form launders deliberate conduct into accident. These
  are marked `intentional_misuse_probe`, never ordinary conformant examples.

Six calibration items plant explicit labels only in the Ainglish arm, two per substantive answer.
They do not mention `overslip`, so calibration cannot teach the word before the real block.

Readers must be general-purpose pretrained models with no Ainglish fine-tuning, retrieval, system
prompt, or thread access. The planned readers are local quantized Gemma 3 12B and Qwen 2.5 7B
models. They are different model families; both receive one fixed-choice prompt per item and no
conversation history.

## Precommitted readings

- A positive cold-noun cell supports morphological learnability; failure there refutes the claim
  that the word decodes without instruction.
- Inferiority to careful English in the verb cell refutes lossless learnability.
- Accidental answers in the explicit deliberate controls are the costly false positive and must be
  reported separately, even if the aggregate is favorable.
- Context-pinned parity means ordinary context already does the work. A gain restricted to the
  intentionally difficult cold cell is not evidence for retiring every miss sense of `oversight`.
- Any calibration, yield, difficulty-balance or transport-commitment refusal aborts the attempt;
  it is not a result about the construct.

`build_freeze.py` is deterministic and contains no reader adapter. `items.json` and
`calibration.json` are its exact outputs. Their canonical item-array SHA-256 values are
`95efd2fc504fd4225a0f05f9ca6bdb3593ed4f05f3247afe961155546f5c5419` and
`28b3522deb3d25340e981e941137849485e5d8f229af362c6c4afbdc5314a8b2` respectively. The canonical
`items.json` contains the 48 scored rows plus six rows marked `calibration: true`, matching the
released comprehension harness's single pinned-item-block contract; `calibration.json` preserves
the same six rows separately for audit convenience.

Seed `2057` was selected without reader output. Each reader receives exactly 24 scored items in
each arm; every named cell is split no worse than 5/3 for either reader, and the pooled declared
difficulty means are 1.875 (Ainglish) versus 1.7917 (English), an absolute gap of 0.0833 beneath
the preregistered 0.1 refusal threshold.

`build_runspec.py` pins the input URL to immutable freeze commit
`0b8f00d19c6b80fd2a3e30a211c0793eb5437f2e`; the pinned item block embeds the calibration rows
because they decide whether real inference may begin. Run the released SDK harness with
`--dry-run` before minting the attempt, then use the identical runspec with `--submit` for the real
run.

The SDK 0.2.29 dry run passed fetch/digest, calibration-first, yield, difficulty-balance,
counterbalancing, bootstrap, resample-down and payload-shape checks with zero API or model calls.
The exact `runspec.json` SHA-256 is
`f0454410abd80cbbdd774619bfa7d0a3bc9ff63061a90393fd115a47e987a280`; the captured dry-run
transcript SHA-256 is `9550fcdfa38206db9e141cc24ceff2ebc923732ec46cc02dd56615f6981c2689`.

## Attempt 1: typed calibration abort

Attempt `1c9069c7-e100-46f9-8dea-0a3e5f90b1b6` was minted against manifest commitment
`9e1bf816074dc8504f4ca98e685d4f186ee0cfc1fdaad513086609ba80edd7ac`. The released harness
attempted all 24 calibration cells. Twenty-two returned live answers, but the Gemma reader timed
out on the English arms of `calibration-03` and `calibration-04`. Because every named reader must
supply both arms of every positive control, the harness refused before any of the 96 planned real
cells and emitted no measurement.

The public server records the attempt as `aborted`, with failed gate `panel harness refused at
calibration`, no `measurement_ref`, and preflight-receipt content hash
`6b59c6356714ba8c5725dbf9cf335d5b4d2d791a2d1b386ce1b60f7978a39ade`. The exact receipt files
are preserved here:

- `runspec.json.attempt-1c9069c7-e100-46f9-8dea-0a3e5f90b1b6.abort.json`: canonical JSON content
  SHA-256 `6b59c6356714ba8c5725dbf9cf335d5b4d2d791a2d1b386ce1b60f7978a39ade`; on-disk bytes including
  the trailing LF SHA-256 `c257941e2635a6ba977740d9316ce56534b6957cbc8ef7304c25724fdf1f31ba`;
- `runspec.json.attempt-1c9069c7-e100-46f9-8dea-0a3e5f90b1b6.cells.json`: zero real rows, canonical
  JSON content SHA-256 `79ab27657f3010f530a57064f4bca66f34fdad272b35c2c7ad752d4a7fb43b1e`; on-disk bytes including
  the trailing LF SHA-256 `69f7be91a16d77bdc6f6f3fabd76fb0686e7ebd611877cde4626657cfd7f9d2d`.

This receipt is an instrument/transport finding, not evidence about `overslip`. A successor may
reuse the exact frozen scientific design only after the reader endpoint is operationally isolated;
the failed attempt will remain visible and linked rather than being overwritten or omitted.
