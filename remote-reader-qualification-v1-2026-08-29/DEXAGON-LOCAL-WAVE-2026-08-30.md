# Dexagon local reader qualification wave — 2026-08-30

This wave prospectively selects two already-installed, distinct base-model lineages for the frozen
remote-reader qualification v1 packet. It downloads no model and does not expose any proposal item.

The selected candidates are:

1. Liquid AI LFM2-24B-A2B, local Ollama artifact
   `sha256:d6c816d74887ed480a3afd5baa2dd2a5987ef6b359b8661e80e1e9fb3501650c`;
2. 01.AI Yi-34B, local Ollama artifact
   `sha256:ff94bc7c1b7a4792e2fb6a9e8d1062e205c97180b18cc93c4ec943961bd8ab53`.

Both artifacts were installed before this qualification kit and its v10-general holdout were
published. Neither lineage appears in an earlier retained run over these packets. Their prior
appearance in the separately frozen agent-task benchmark is used only to avoid selecting a reader
with an obviously broken task transport; those Ainglish-bearing benchmark results are not a
qualification result and are not proposal evidence.

Both development plans are frozen and published before either candidate is called. Every selected
development plan is then run once regardless of the other candidate's result. A candidate reaches
the common holdout only if its own development result passes the frozen gate. Every result and
journal is retained, favourable or adverse. The scientific reader gate opens only if two genuinely
distinct lineages pass the same holdout; one passing reader is not padded with aliases, quantisations,
or a second tag from its family.

The two candidate records disclose community-quantisation provenance limits. The local Ollama
catalog binding and artifact digest are checked before the wave; a later measurement must bind the
exact artifact again in its own preregistration.

## Result

Both candidates were excluded at the format gate on their single frozen development run. Neither
reader saw any of the 24 semantic development items, the 64-item common holdout, or a proposal item.

| Candidate | Exact one-code controls | Truncated controls | Semantic calls | Verdict |
|---|---:|---:|---:|---|
| LFM2-24B-A2B Q4_K_M | 6/12 | 0 | 0 | excluded |
| Yi-34B Q4_0 | 6/12 | 5 | 0 | excluded |

LFM2 returned the literal string `None` for alternate control phrasings. Yi sometimes followed the
one-code instruction but otherwise continued after the code until the 16-token bound. These are
transport/instruction-following failures under the frozen instrument, not evidence that either
model does or does not understand an Ainglish construct. The adverse results are retained; changing
the prompts or token bound after seeing them would be a new development instrument, not a retry.

The general reader gate therefore remains closed. No holdout plan was created, no Ainglish attempt
was minted, and no proposal measurement was filed from this wave.
