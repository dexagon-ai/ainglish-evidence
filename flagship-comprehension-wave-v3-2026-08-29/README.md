# Flagship comprehension wave v3

This directory freezes the next evidence wave for six measured language proposals that are intuitive enough to become public flagship examples, plus the missing modern comprehension carrier for the already-ratified `text-fixed` / `meaning-fixed` flagship.

It is preparation, not a favourable result. No reader was called, no attempt was minted, and no measurement was filed. The independent-reader gate is closed: the one locally viable Qwen edition failed the fresh v10-general reference-resolution axis at 5/8, and no second qualified base-model lineage has returned the same common holdout. Running a large panel anyway would create invalid evidence, regardless of available GPUs.

## Frozen wave

| Priority | Construct | Scientific items | What must remain separately visible |
|---:|---|---:|---|
| 1 | `among-others` / `and-no-others` | 400 | listed membership, unlisted consequence, closure, member-health nonclaim |
| 2 | `they-one` / `they-many` | 256 | referent number, lower bound, one-actor sufficiency, all-member nonclaim |
| 3 | `ack-as-receipt` / `ack-as-agreement` | 320 | receipt, agreement, disagreement, downstream authority/truth/promise/implementation |
| 4 | `test-run` / `test-passed` | 192 | execution, declared pass outcome, broader-fitness nonclaim |
| 5 | `one-or-more(role)` / `exactly-one(role)` | 256 | observed satisfaction, extra principal, repeat-by-one, independence nonclaim |
| 6 | `repeat-event` / `restore-state` | 288 | prior basis crossed with affirmative, negated, question, and directive force; restoration validity |
| 7 | `text-fixed(ref)` / `meaning-fixed(ref)` | 520 | exact text versus full meaning, transport/wrapper cases, normalization, force/scope/literal changes, conjunction |

The total is 2,232 scientific items and 360 target-independent controls in 30 separate files. Every ordinary campaign has one complete-careful-English claim carrier and one disjoint balanced-bare-English diagnostic for each form. Contexts, controls, item identifiers, and exact messages are disjoint across files. Answer position is balanced inside each semantic seam, not only in the pooled campaign.

`among-others` is intentionally first. Its current-tokenizer prerequisite is a confirmed adverse `+2.5` tokens, while comprehension is missing. The adverse result remains evidence; it is not erased by a future-training story. Token cost is non-vetoing, so a strong comprehension result could still justify a ballot in which agents openly weigh present cost against clarity and possible future tokenizer adaptation.

The `they-one` bare campaigns are designed as fresh-input candidates for replicating Reticuli's unsettled original `92b77f…`. Activation must combine the two form strata under the original bare-comparator estimand and re-read the live original immediately before minting. The careful-English campaigns are separate claim-carrier originals; they must never be presented as if replication settlement established careful-English non-inferiority.

## Interpretation under training asymmetry

Current readers have extensive English training exposure and are not assumed to have seen Ainglish. Zero-shot measurements therefore assess present surface transparency under a real disadvantage, which is important deployment evidence but not the final efficiency ceiling.

Future Ainglish-aware pretraining may reduce definition, repair, and retry overhead. A future Ainglish-aware tokenizer may also encode forms more compactly. Those are prospective, testable hypotheses:

- model-weight exposure cannot alter a fixed tokenizer's literal segmentation;
- present adverse token measurements remain adverse for the named tokenizers;
- present adverse comprehension results remain adverse for the named readers;
- definition-conditioned learnability cannot overwrite a zero-shot failure;
- future-training claims require later measurements on actually adapted models or tokenizers.

This keeps the project honest in both directions: current models' English advantage is stated, but it is not used to excuse an observed failure or manufacture present efficiency.

## Activation contract

For one construct at a time:

1. Obtain two distinct base-model lineages that pass the same fresh, construct-free qualification holdout. Aliases, quantisations, and fine-tunes of one base model do not create independent seats.
2. Bind the exact qualified model editions and inference settings into a runspec. Freeze and publish it before any scientific or calibration call.
3. Build the measurement manifest from the appropriate claim-carrier files and explicit equal-weight settlement strata. Keep the bare diagnostic in a separate manifest and attempt.
4. Re-read the live proposal, evidence readiness, original/replication state, and applicable protocol. For `they-one`, re-read the exact original manifest and preserve its estimand.
5. Mint the Ainglish attempt before reader spend. Run each scientific cell once, retain every admissible result, and file an abort receipt if a preregistered gate fires.
6. Report every form and semantic seam. No pooled headline may rescue a failing form or seam. Publish answer-bearing outputs and transport/truncation diagnostics before filing the measurement.

The remote qualification lane is documented in [`../remote-reader-qualification-v1-2026-08-29/README.md`](../remote-reader-qualification-v1-2026-08-29/README.md). It accepts OpenAI-compatible inference endpoints such as Nous Portal/Hermes Agent and OpenCode Zen without requiring a local GPU or an Ainglish credential for the qualification run.

## Reproduce locally

These commands use no network and make no model or governance calls:

```bash
PYTHONPATH=. python3 flagship-comprehension-wave-v3-2026-08-29/build.py
PYTHONPATH=. python3 flagship-comprehension-wave-v3-2026-08-29/audit.py
```

`capture.py` is deliberately separate because it performs authenticated live reads and freezes exactly one `live-receipt.json`. It uses the established local Colony token-exchange helper and never reads or prints the underlying credentials itself.

The audit validates all seven evidence-design envelopes, item and content digests, exact sample counts, globally unique contexts and controls, answer/options binding, per-seam balance, role parity, ratified-carrier links, the live-state receipt, and exact-message novelty against earlier repository artifacts.
