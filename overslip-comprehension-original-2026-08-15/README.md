# `overslip` comprehension original

Status: **item bytes frozen; zero reader calls; no Ainglish attempt minted yet**.

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
`d294fcd2b737579ffbfd5b2f3080894e3f9e7c96b7b67b4604bab0a1cae3635d` and
`f1fa120eee854c9ec347872cd60f685a240e70859c3dfefb2653f4282740930b` respectively.

Seed `2057` was selected without reader output. Each reader receives exactly 24 scored items in
each arm; every named cell is split no worse than 5/3 for either reader, and the pooled declared
difficulty means are 1.875 (Ainglish) versus 1.7917 (English), an absolute gap of 0.0833 beneath
the preregistered 0.1 refusal threshold.
