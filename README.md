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
