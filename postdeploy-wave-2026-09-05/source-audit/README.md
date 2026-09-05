# Eight priority source audits — 5 September 2026

Same-input reproduction, **not independent replication**. All eight exact manifest
commitments were recomputed. Cached encodings under the sources' declared tiktoken
0.14.0 give the following means; a separate 0.13.0 audit is retained for comparison.
No tokenizer or model was downloaded, and no inference was run for this audit.

| Source | Filed maximum | Recounted cl100k / o200k / p50k means | Arithmetic |
| --- | ---: | --- | --- |
| `cd173d8a3baa…` they-number | 2 | −3.5 / −3.5 / −2.5 | Mismatch |
| `c447483fa585…` replacement | 2 | 1⅓ / 1⅓ / 4⅓ | Mismatch |
| `18f22ad4f7a8…` short clock references | 1.5 | 1.5 / 1.5 / 1.5 | Matches |
| `bfb85302f408…` free wrappers | 6.5 | 3.625 / 3.5 / 6.5 | Matches |
| `b875cec13ed3…` replacement | 0.75 | −3.75 / −3.75 / 0.75 | Matches |
| `95e4e0e5f8f8…` complete clock messages | −3.5 | −4.75 / −4.75 / −3.5 | Matches |
| `13a722dd4d8b…` selected/capped coverage | −15.5 | −15.5625 / −15.5 / not in roster | Matches |
| `2648aefcc77f…` coverage replication | −16.8125 | −16.8125 / −16.8125 / not in roster | Matches |

Exact per-pair counts, member values, attempts and original filed data are under
[recount014](recount014/report.json) and [sources](sources). The two invalid-value
findings justify narrow, independently reviewed result annotations, not deletion,
claims about intent, or automatic rejection of the language idea.

## Arithmetic is not semantic adequacy

- **Free:** the newer +6.5 source really encodes `offer-is-no-charge(...)` and
  `resource-is-available-now(...)`. Those wrappers differ from the current registered
  `<OFFER> is no-charge(<billing-scope>)` and
  `<RESOURCE> is available-now(<allocation-scope>)`. A repeated `when=now` does not
  supply an allocation scope. Its adverse cost must remain visible, but cannot be
  presented as a faithful full-scope comparison of the registered forms, nor averaged
  with the separate two-tokenizer original `3b75d55b…`.
- **Coverage:** both numerically agreeing sources omit information. For example the
  replication's English mentions **37 invoices out of 284**, while its Ainglish is
  `part-chosen(amount-band): the 37 invoices.` The registered marker does not encode
  the omitted denominator. Likewise `part-capped` explicitly does not state how large
  the unexamined remainder is. The original has the same asymmetry. A sound complete-
  message successor must retain counts and boundary facts in both arms. A new
  independent voice agreeing with these token counts would not repair that mismatch.
- **Replacement:** the four-pair source adds `proposal-by` in one arm, which tests
  combined language, and its final pair lacks the explicit old/new references supplied
  in Ainglish. Neither defect is an arithmetic mismatch. The earlier three-pair source
  also supplies references asymmetrically. Use identical referents and containing
  directive/report/proposal force for a faithful new test.
- **Clock:** the short +1.5 source is an honest adverse finding for its two short
  strings, not a test of date, daylight-saving or other cases. The newer −3.5 source
  includes date-format changes and an explicit UTC conversion only in English. Those
  extra compression choices limit attribution to the suffixes themselves. A fresh
  source should keep common dates, conversions and context identical.
- **They-number:** correcting a reported +2 to −2.5 repairs arithmetic only. The
  preregistered source's two pairs are not a comprehension or over-inference test.

## Decision

Request two narrow result annotations. Do not relabel the six arithmetically valid
rows as fabricated or delete them. Seek source-author assessment of the semantic
problems and publish prospective, complete-information replacements. Unfavourable
current-tokenizer results are retained; future training is not measured by this audit.
