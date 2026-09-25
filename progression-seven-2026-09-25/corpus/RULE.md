# Recoverable source domains, fixed before acquisition

This is a bounded purposive corpus, not a representative sample of human or agent
communication, and not a measurement. Selection is based on domain relevance,
never on whether an Ainglish rewrite wins. No reader or tokenizer calls.

1. CPython 3.13.7, commit bcee1c322115c581da27600f2ae55e5439c027eb:
   acquire complete `Doc/whatsnew/3.12.rst`, `Doc/whatsnew/3.13.rst`,
   `Doc/using/cmdline.rst`, `Doc/library/configparser.rst`, plus `LICENSE`,
   `Doc/license.rst`, and `Doc/copyright.rst`.
2. SciPy 1.16.2, commit b1296b9b4393e251511fe8fdd3e58c22a1124899:
   acquire every direct `.rst` file in `doc/source/tutorial/stats/`, sorted by
   path, plus `LICENSE.txt`. No recursive subdirectories, code, images or datasets.
   Preserve additional local notices in each file. Refuse more than 80 files,
   more than 2 MiB per file or 8 MiB total; do not silently truncate or subsample.
3. Preserve bytes, Git blob hash, SHA-256, URL, full source context and this rule.
   Extract blank-line-delimited blocks starting with an ASCII letter, containing
   15–160 whitespace words. Retain markup verbatim; no invented plain-text
   normalisation. Indented code/directives, headings, tables and list starts are
   excluded by that explicit rule. This is a narrow extraction and is not a
   language gold bank. Each block retains line offsets into its complete source.
4. Retain all blocks as background. The candidate slice contains ALL matches of
   case-insensitive whole words `last|latest|final|default|assigned|significant|important`.
   No collision threshold, difficulty filter, handpicked deletion or score-based
   reranking. Sort by repository, path, starting line. A zero-hit result stands.
5. This archive is PSF-licensed and BSD-3-Clause-licensed upstream documentation,
   with notices retained, NOT CC0. The only transformation is the separately
   stored extraction described above. It must not enter an Ainglish public-domain
   language release. Source reports/examples may contain domain claims; these are
   source text, not endorsed findings or validated Ainglish answer keys.

Before any scientific use: choose a prospectively scoped natural communication
task, recover any cross-referenced meaning-bearing context, independently review
arm-specific golds and complete counterparts, and freeze exclusions and population.
These source domains do not themselves satisfy the pending comparator protocol's
background-collision or carrier requirements.
