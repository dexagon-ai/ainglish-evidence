# Frozen run protocol

## Question

Which of six live, human-readable candidate distinctions are presently transparent to diverse
unadapted local model families, which become usable after one exact definition card, which are
fragile to benign surface damage, and which merit amendment before scarce qualified-reader capacity
is spent?

## Population

- Six proposal versions captured from the live register before item construction.
- Eight author-designed operational frames per proposal.
- Five isolated conditions per frame.
- Six exact, already-installed Ollama artifacts from distinct declared model families.
- 180 calls and 1,440 scored cells.

The frames are development-only. They are not sampled from, or reusable in, a governance carrier.

## Estimands

For each construct, report complete-population accuracy by condition across all model/cell pairs,
plus every model-specific 8-cell result. The primary contrasts are:

- cold Ainglish minus careful English;
- definition-conditioned minus cold Ainglish; and
- corrupted minus canonical cold Ainglish.

Bare-English accuracy measures correct recognition of missing semantic information. It is reported
separately and is not subtracted from marked accuracy as though bare text carried a hidden answer.

Invalid batches remain in every denominator. There are no inference retries, prompt repairs,
reader substitutions, exclusions, or post-result relabelling.

## Prospective classification

Classification is model-facing development triage, not a human-intuitiveness or governance label.
Thresholds use aggregate complete-population accuracies for each construct:

- `amendment_candidate` if definition-conditioned accuracy is below 0.75, careful-English accuracy
  is below 0.80, or cold Ainglish is below 0.60;
- otherwise `strong` if cold is at least 0.80, careful English at least 0.85, definition-conditioned
  at least 0.85, corrupted at least 0.75, and cold trails careful English by no more than 0.10;
- otherwise `fragile` if corruption trails cold by at least 0.15 or at least two readers score below
  0.50 on cold Ainglish;
- otherwise `learnable` if definition-conditioned accuracy is at least 0.80 and improves on cold by
  at least 0.10;
- otherwise `amendment_candidate` because the finite battery does not establish a stable strength.

Independent flags accompany the primary class: `cold_careful_gap`, `definition_gain`,
`corruption_drop`, `bare_ambiguity_failure`, `reader_heterogeneity`, and `invalid_channel`.
Their frozen thresholds are respectively cold-minus-careful below -0.10, defined-minus-cold at
least +0.10, corrupted-minus-cold at most -0.15, bare accuracy below 0.75, a cold reader range of at
least 0.375, and one or more invalid cells.

## Integrity and stopping

1. Capture exact proposal fields and installed-model digests.
2. Generate and audit all prompts, item labels, option permutations, checksums, and the run plan.
3. Commit and publish the packet to `origin/main` before any model call.
4. Refuse if a preregistered digest, proposal pin, model tag, or model digest drifts.
5. A process interruption records the in-flight batch as invalid on resume; it is never rerun.
6. Retain content, thinking, timing, usage, parse errors, and complete Ollama receipts.
7. Publish favourable, null, adverse, and channel-failure outcomes alike.

No result changes proposal state or enters the Ainglish measurement API.
