# A real offline ingestion rehearsal, not an adoption claim

The existing published v3 pack was pinned at manifest SHA-256
`b1031f56b308390de8f2a5eaa5c902c6bb62fea34cb9289dcaed7701a5c69b5c`
and processed through the current SDK ingestion implementation. No pack files
changed and no model was downloaded or trained.

Canonical filtering retains69instruction rows,21parallel pairs and27complete
definition documents. Opting into explicitly non-normative examples gives153
instructions and63pairs; it does not change27definition documents. Every kept
source row remains byte-value equivalent after JSON decoding, with provenance.

The actual CLI excluded three deliberately copied public training rows used as
test canaries, leaving66canonical instructions. Those became content-preserving
user/assistant chat envelopes. The canaries test exclusion plumbing, not an
independent holdout. Exact deduplication cannot detect unknown paraphrase or
template leakage, and the test proves hyphen removal is not treated as identity.

Wrong pins, unknown slugs and an existing output directory were correctly
refused. `RESULTS.json`, the six projection receipts, CLI receipt and preserved
records make the rehearsal inspectable. This is neither a new language release
nor evidence that an external corpus or AI lab included or trained on the pack.
