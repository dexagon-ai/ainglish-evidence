# Matched cold versus brief-reference transfer study

Prospectively designed on 5 September 2026, before reader calls. Two familiar ratified pairs:
`fact-not-known / choice-not-made` and `no-delegation / one-hop-delegation-allowed`.
This is a controlled **reference-assisted transfer** study, not weight training, persistent
learning, future-tokenizer simulation, an independent replication, or a replacement for adverse
historical cold/reference results. Earlier project studies tested these conditions on different
sets. Here the new base cases, questions, options, readers and arm assignment are matched between
conditions, permitting a within-case exposure contrast.

## Fixed design

- Two constructs × two exposures (`cold`, `brief-reference`) × 256 real cases × two fixed
  already-qualified local reader lineages = **2,048 real calls**. Four panels each also have
  eight target-independent positive controls, exposed in both arms to both readers = 128
  control calls. Total ceiling: **2,176 calls**, no extensions or retries.
- Each construct has 128 cases per registered form. The 128 paired form-frames cross eight
  domains with eight contexts/operations and two authority/root variants. Gold is fixed by the
  declared mapping and a deterministic truth table, before readers. Opaque option positions
  are balanced within each form and shuffled by a fixed seed independently of domain/operation;
  a wrong but legal option remains a scientific error, not an instrument fault.
- A stateless call receives one arm of each item, using the SDK's fixed seed/reader/item deal.
  The same seed and item IDs preserve each reader's arm between cold and reference conditions.
  No reader sees its earlier answer or a held-out answer key.
- The reference is 150 words for fact/choice and 140 for delegation. It appears identically
  before **both** English and Ainglish in the reference condition, including controls. Therefore
  it does not secretly provide the marked arm with extra ground truth. Its orchard/music
  examples do not occur in the held-out operational cases or their questions.
- Test order is fixed: fact/choice cold, delegation reference, fact/choice reference, delegation
  cold. This counterbalances exposure order between constructs; it does not eliminate time
  effects. Every condition is a separate public original under its own committed manifest.
- Readers: the exact qualified Mistral Small 3.2 24B Q4 and Gemma 3 12B Q4 local artifacts/settings
  from `reader-qualification-local-v1-2026-09-04`. They are two fixed lineages, **one Dexagon
  principal**, not a random model population or an independent confirmation.
- Instrument: source-pinned SDK safeguard PR163 at e5ec787, clearly identified as an unreleased
  instrument revision until publication. It adds prospective refusals; it changes no scorer or
  proposal threshold. No new models or tokenizer vocabularies may be downloaded.

## Admissibility before spend

All input bytes, semantic gold, option positions, guides, settings, stopping rules and analysis
are published in a commit before any reader call. Each exact attempt is preflighted and minted
before its first calibration cell. Every reader must pass the fixed planted gap of at least 0.5.
Zero off-option, absent, truncated or transport-fault cells are allowed, including controls and
already-started concurrent calls. The SDK enforces this; the protocol is not just free text.
Any such breach aborts that panel with partial records; there is no rerun or sample substitution.
Other predeclared panels may proceed, but a missing condition prevents that construct's paired
exposure conclusion. A legal wrong target answer never triggers a calibration failure.

Each proposal must still be published and ratified, with unchanged mapping, and its existing
cost prerequisite must remain supported before the corresponding spend. GPUs must be free of
another loaded inference workload at the campaign start; no other models are unloaded. Every
finite admitted direction is filed once, including adverse/null results. Submission failure is
recovered from retained output, not by rerunning inference.

## Analysis fixed before calls

The four register measurements report `comprehension_accuracy_delta` (Ainglish minus complete
careful English), each form separately, with retained arm accuracies, reader results and the
SDK's conditional item-bootstrap interval. Calibration accuracy is never the target outcome.

The report-only exposure contrast is **(Ainglish minus English with reference) minus (Ainglish
minus English cold)**, preserving paired reader/item/arm cells. Show each arm's own improvement,
not merely an attractive net difference. Resample 128 base-frame clusters (keeping both forms
and both readers together), 2,000 bootstrap draws with seed 2026090541, for conditional 95%
intervals. Also show all eight domain results and per-form intervals; no pooling away a losing
form. This contrast is not submitted under an invented register metric.

For interpretation, a form clears the advertised -5 pp non-inferiority margin only if its entire
reported interval is above that margin; unresolved or adverse is reported as such. Absolute arm
accuracy and the protocol floor are separate. A positive exposure effect cannot erase an adverse
cold result or prove full normative-contract completion.

Error tables separate fact/choice existence-versus-resolution confusion and delegation permission
expansion, over-restriction, forbidden extra hops and transferred accountability. Rows retain
every legal wrong answer and every refused cell. Count the exact guide's bytes, words and cost on
the three cached reference encodings; these are **reference-tokenizer overhead**, not the local
readers' billed token counts. Because the guide is repeated per stateless call, do not claim its
cost is amortised or removed after training.

## Limits and semantic review

The fact/choice set tests the core two-part resolution distinction, not all out-of-scope states,
false marker assertions, human authority inference, robustness attacks or post-ratification use.
Delegation tests eight explicit operation classes, plural roots and three-part permission/depth/
accountability recovery; it does not observe hidden handoffs or enforce a security policy.
Neither study is a complete human-validation campaign or a claim about all naturally occurring
messages. Repeated templates and only eight domains limit generalisation; intervals are
conditional on this authored frame and these fixed readers.

Pre-reader semantic review caught a draft contextual mismatch: an exclusion context originally
asked which option applied. Review also caught globally balanced answer positions that were
not balanced within each form. The final `frozen-v2/` corpus corrects the exclusion question
and uses fixed shuffled, within-form-balanced answer positions. No draft was observed by a
reader, counted, preregistered or published as evidence. Only `frozen-v2/` inputs are eligible
for this study; `build.py` reproduces them from source.
