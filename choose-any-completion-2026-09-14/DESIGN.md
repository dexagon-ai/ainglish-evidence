# Review-draft design

This is a **new original**, not a replication of the old 32-item instrument. It asks a different,
more complete joint question. It must never set `replicates_hash` to that smaller study.

## Population and responses

The initial draft has exactly 144 authored worlds, 72 per form, 12 per form/domain. Every world
specifies a frozen set of 2–8 distinct identities, an excluded identity, and a unique criterion
ordering. Its five candidate procedures are:

- always return the first identity;
- always return the identity with the lowest stated criterion score;
- give the first identity weight two and every other identity weight one;
- return each identity with probability exactly 1/N;
- always return the explicitly excluded identity.

All return exactly one result. For `choose-any`, the first four comply. For `draw-uniform`, only
the fourth complies. All probabilities are exact rational numbers; N is never one, where the
distinction between constant and equal-probability selection would collapse.

The four claim statements concern one eligible result, equal odds on this draw, resistance to
prediction by an informed adversary, and independence of a later draw. Only the first is entailed
by `choose-any`; the first two are entailed by `draw-uniform`. A permitted implementation's extra
properties are not promises of the instruction itself. No realised single outcome is used to
judge a distribution.

The two probes are two selections of a **complete set of labels**, not two unrelated reader calls.
One proposed policy set is correct and another changes one policy membership. One guarantee set
is correct and another changes one claim membership. Their Cartesian product gives four unique
answer records. Partial scores are decoded from the selected record, and exact joint accuracy is
the official panel's ordinary single-answer accuracy. This avoids multiplying marginal accuracies
or pairing two differently counterbalanced cells after the fact.

The answer record never occurs in either presented arm. Questions ask implementation consequences
and permitted auditor claims, not “which marker means X?”. Label order and answer position vary;
answer position is balanced within each form and decoupled from the guarantee contrast.

## Comparator review remains required

Both arms carry identical scenario facts, scores, set/version identity and excluded identity. Only
the request differs. The English request expands the construct's complete relevant commitment,
including the absence of additional guarantees. This is an authored per-form rendering of the
live mapping, **not a claim that the entire combined register paragraph was copied verbatim**.
The author/reviewer must approve these exact expansions against the current comparator protocol
before launch, or replace them prospectively. No omission may manufacture an Ainglish advantage.

Bare “random” is not an accuracy comparator here. A bare arm could be a separately specified
descriptive ambiguity study; it is not needed to turn a parity result into a positive CAD result.

## Analysis specification to settle before the final freeze

1. Primary official scalar: equal-weight mean of the two per-form joint exact-answer accuracy
   differences, in percentage points, Ainglish minus complete careful English. Preserve both form
   rows and the SDK's interval/resolution/calibration/yield reports unchanged.
2. Publish exact joint, implementation-only and guarantee-only accuracy per arm, form, reader and
   domain. Publish each of the five policy decisions and four guarantee decisions. Every error and
   typed absence remains visible; the official dead-cell policy is not replaced by this report.
3. For an over-inference rate, show both the whole-sample rate and the number of cells actually
   offered the contrary claim. A claim never offered as an alternative cannot be counted as a
   tested rejection. Report denominator/uncertainty; do not hide empty or small cells.
4. For preservation, a separate one-sided lower confidence bound on each form's difference must
   clear −5 pp before a confidence-backed NI claim. A non-significant loss is not sufficient.
   Absolute ≥90% success targets, <85% refuters and >10% error refuters remain separate declarations.
   Values in the 85–90% zone are not a success merely because the explicit failure threshold was
   not crossed. Reporting a point estimate and claiming a confidence bound are different acts.
5. An item-bootstrap interval of [0,0] at a perfect tie is not a population-level NI certificate.
   Publish a finite-sample boundary sensitivity rather than pretending zero observed errors means
   zero possible errors. The installed generic CAD resolution rule still applies.
6. The final analysis must specify how reader-within-world and frame-family correlation is treated.
   The SDK resamples worlds/items; a supplementary frame-family sensitivity and per-reader table
   should be frozen too. Any binomial/normal planning calculation states its IID assumptions.
   No method may be chosen after looking at the target responses. The exact supplementary NI
   interval method is an OPEN review decision, not silently settled by this draft.

Because both forms must pass, a favourable pooled result cannot compensate for a failing form.
The official result and any report-only analysis must name their different estimands and scope;
do not replace an official interval or manufacture a settlement agreement from a threshold pass.

## Power and sample alternatives

Run `python prospective_power.py`. Under an ideal independent-cell planning model at 95% accuracy
in both arms, 144 worlds/two readers give about 39% NI power per form. The same model gives about
90% per form at 660 worlds. At 90% true accuracy, roughly 1,236 worlds are needed by that model.
These are sensitivities, not promises: the 12 authored frame families are correlated and two
endpoints are not automatically two independent reader lineages.

The generator can produce a larger balanced draft. Its larger output contains the original 144
worlds, so **it is not a fresh replication**. A sample choice is made once before any target calls;
there is no run-small, inspect, expand rule. Merely repeating frames cannot be sold as equivalent
to collecting independently diverse natural messages.

## Runtime boundary

Available local artifacts were inspected without loading them: Mistral Small 3.2 24B Q4_K_M
(`6629ee92de51…`) and Gemma 3 12B Q4_K_M (`de1f65ea3438…`). They are candidate lineages, not a
qualified or reserved roster. The machine also has Qwen 3.5 9B; no new model is needed or requested.

Use the latest installed SDK's official reader-qualification and panel workflow. A real run needs:
fresh exact model/precision/settings bindings, target-independent per-reader qualifications,
passing pre-spend structural/calibration gates, immutable final item and analysis pins, live
proposal/protocol/role checks, and `mint_attempt` before the first target cell. Never unload
another participant's model or retry until a favourable result appears. Raw stateless reader
cells must not receive the drafting agent's context, keys or answer metadata.

The draft has no live runspec and no qualification receipt. The synthetic oracle check forbids
network sockets and cannot qualify readers or establish language quality.
