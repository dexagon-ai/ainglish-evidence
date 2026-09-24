# Source corpus rule v1 — fixed before acquisition

This is a narrow **technical-English source corpus**, not a representative sample
of all English, agent conversations or Ainglish's three candidate populations.
No reader answers, tokenizer results or ambiguity scores inform selection.

Source: CPython v3.13.7, commit
`bcee1c322115c581da27600f2ae55e5439c027eb`. Enumerate every directly contained
`Doc/tutorial/*.rst` file from that immutable Git tree, sort by full path, retain
every source byte and its Git blob identity and SHA-256. Also retain LICENSE,
Doc/license.rst and Doc/copyright.rst. No per-file topic selection or quota.

Derivation: split each tutorial source on blank lines. Retain blocks whose first
line starts with an ASCII letter, with no indented line, no RST role/link/code
backtick, directive marker, or line made solely of heading punctuation. Join
physical lines with one space; retain blocks with 15–120 whitespace-delimited
words. This deliberately conservative lexical rule misses much valid prose and
is NOT an RST parser. Preserve full source files and line coordinates to recover
context. Sort by (source path, first line); no random sample or outcome selection.

The complete retained paragraph population is the corpus. A separate candidate
slice retains every paragraph containing a case-insensitive whole-word match
for `last|latest|final|default|assigned|significant|important`. Empty topics stay
empty. This lexical slice does not label ambiguity or intention and is not a
proposal's registered corpus-based carrier. It does not create a favourable
English comparator, answer key, or marked translation. Those would require a
new prospective design, independently recoverable annotation and semantic review.

Digest recipe: raw source SHA-256; manifest/source inventory canonical JSON;
paragraph arrays canonical JSON (`sort_keys=True`, compact separators,
`ensure_ascii=False`, no non-finite numbers). Source ordering and line positions
break all ties. No Ainglish discussion or newly authored prose enters the corpus.

Rights: source software **and documentation** are PSF License Version 2, with
historic notices retained in upstream LICENSE. See
https://docs.python.org/3/license.html and the pinned LICENSE. Retain the full
notices with every redistributed source/derived slice. These external texts are
**not CC0 and not part of an Ainglish public-domain language release**.
Changes are solely deterministic paragraph extraction, line joining, filtering,
indexing and digest metadata; source files are unmodified. No PSF endorsement.

Acquisition limits: at most 40 tutorial files, each at most 1 MiB, total at most
8 MiB. Refuse incomplete tree or unexpected content; do not silently truncate.
No model download. Offline recovery compares every source digest and both full
and selected arrays, not only the selected slice's hash.
