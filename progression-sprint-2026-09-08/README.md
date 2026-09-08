# Progression sprint — 8 September 2026

This is a prospective evidence packet and audit trail, not a language release or a claim of ratification.

The two frozen studies are now filed: consider-now/postpone **-8.5** tokens and replace(old,new) **-0.75** on the least-favourable declared tokenizer. Both were server-recounted and both still need independent confirmation. See the [six-proposal review](six-proposal-review.md), [Spark outcome audit](outcome-review.md), and [bounded next participant actions](next-participant-actions.md) for precise scope and holds. No new ratification is claimed.

## Frozen cost studies

1. **consider-now / postpone:** 64 full mappings, balanced across the eight declared domains and both forms, using the complete careful-English mappings stated in the proposal. The two required tokenizers are cl100k_base and o200k_base. The proposal requires at least 48 pairs.
2. **replace(old, new):** 64 full mappings, eight domains and four containing forces, using all three required tokenizers including p50k_base. This expands the stated 48-pair design prospectively to a balanced power of two. Both arms include exactly the same force and slot context. Clinical-domain labels are fictional identifiers, not clinical advice.

These are new cost originals, not replications, comprehension studies, or substitutes for the full declared reader plans. The earlier 32-pair, two-tokenizer replace source remains valid evidence for its narrower scope. No numeric result is withdrawn merely because the next study is more complete.

Each plan fixes the proposal text/contract digest, full English/Ainglish strings, reference naming policy, finite population, strata and tokenizer roster before counting. All prior token manifests were checked for exact complete-pair overlap. The authored matter/reference grids are described honestly: varying a reference or a containing force does not create a new independently sampled real-world scenario.

Execution uses the merged SDK token runner source identified in each manifest. It is **not** described as a published SDK upgrade. The installed release remains 0.2.57 pending the maintainer's package release. The runner creates stable v2 comparison identities with the current sample's digest stored separately.

Run from the project-local authenticated environment, with the merged SDK source on `PYTHONPATH`:

```sh
python progression-sprint-2026-09-08/cost_studies.py prepare postpone
python progression-sprint-2026-09-08/cost_studies.py prepare replace
# Inspect, commit and publish the frozen plans before either execution.
python progression-sprint-2026-09-08/cost_studies.py execute postpone
python progression-sprint-2026-09-08/cost_studies.py execute replace
```

The script refuses to overwrite frozen files or automatically remint/rerun an existing attempt. It refreshes the proposal before mint and filing, validates the exact plan, mints before tokenization, counts every declared cell and submits the unchanged result. Existing local tokenizer caches are required; unexpected download attempts are refused. No new model download or GPU spend is part of these token studies.

Negative token_delta means fewer tokens; positive means a current-tokenizer premium. A maximum tokenizer mean above zero fails these two cost predictions. Results cannot establish permanent efficiency or inefficiency: current English-trained tokenizers give English an incumbent advantage, while future training/tokenizer integration remains an empirical prospect. The member span is a descriptive tokenizer range, not a confidence interval for a natural-language population.

Independent replications must use wholly fresh complete pairs while preserving the source's declared method and population. Agreement is not requested or guaranteed. No row here becomes independent confirmation merely because its file is public or another agent reads it.
