# Five-workstream integrity audit

`audit.py` independently rechecks the frozen artefacts for the reader, proxy, evidential-tag,
modal/operational, and ratified-census workstreams. It makes no network, governance, tokenizer, or
model call. The generated `report.json` verifies canonical content commitments, item counts,
form balance, answer membership, unique IDs, calibration counts, byte-identical reference cards,
completed token attempts, and the phase-A reader-result digest.

This is a build-integrity receipt, not language evidence and not an independent replication.
