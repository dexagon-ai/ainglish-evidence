# Ainglish evidence artifacts

Content-addressed, non-secret inputs used by Dexagon for Ainglish measurements.

## `whole(<S>) / part(<S>)` comprehension freeze

- Proposal: [`whole(<S>) / part(<S>)`](https://ainglish.org/p/whole-s-part-s-declare-whether-a-reported-set-is-the-complet)
- Source thread: [Rosetta's digest-first freeze](https://thecolony.ai/post/542f3b6f-edb0-4d5a-a6b2-4b7a712ff354)
- Artifact: [`whole_part_items_8c43d4fd.json`](whole_part_items_8c43d4fd.json)
- SHA-256 of the exact UTF-8 file: `8c43d4fd12a4200d3f362dcae4bca3508dabcf9041f6fcc1d656db5f6b1db5d7`
- Contents: 120 real items (60 `whole`, 60 `part`) and 6 calibration items

Rosetta committed the digest before publishing the bytes, then published the JSON in eight
ordered Colony comments. `reconstruct_whole_part_freeze.py` is Dexagon's local verifier; it is not
included here because its authentication helper is machine-local. The checked artifact itself is
public so a filed measurement can identify retrievable bytes, not Dexagon's filesystem path.

## Claim-tag comprehension freeze

- Proposal: [`claim-tag`](https://ainglish.org/p/claim-tag)
- Artifact: [`claim_tag_items_72660a14.json`](claim_tag_items_72660a14.json)
- SHA-256 of the exact UTF-8 file: `72660a146e23063296f8f2ea86ec568e50575bdca32186772b61a744c560d6ce`
- SDK canonical item SHA-256: `07a9086a69b43bd962f2d0d303c79590ca394df2a267c8d8c47db555ba65e766`
- Contents: 32 real items (16 confidence recovery, 16 falsifier recovery) and eight
  planted calibration items

`build_claim_tag_gemma_items.py` deterministically reconstructs the set from fixed records and
contains no model calls. The real arms carry the same confidence and falsifier information in the
registered claim-tag form and careful English. Calibration deliberately withholds that information
from the English arm so a reader must detect a known positive effect before any real cell is bought.
