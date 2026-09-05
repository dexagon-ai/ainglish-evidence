# Contributor-wide token arithmetic audit, 5 September 2026

This read-only audit covers the public cursor snapshot of **682 token measurements**,
ending at measurement ID 1007. It includes all contributors returned by that filter,
not just one contributor's problematic batch. It makes no governance writes and uses
only the three already cached reference encodings; no models or vocabularies are downloaded.

| Result | Records | Meaning |
|---|---:|---|
| Numeric match | 295 | Headline and declared member/stratum values reproduce within historical four-decimal rounding |
| Coarse rounding only | 46 | Difference is consistent with the older three-decimal convention |
| Numerical mismatch candidate | 71 | Exceeds those rounding explanations; requires exact-target review |
| Not reproduced by this tool | 270 | Unsupported/ambiguous roster, legacy commitment projection, or incomplete carrier; not proof of incorrect evidence |

Of the 71 candidates **at the snapshot time**, 35 were already excluded (33 result-invalid,
one instrument-invalid, one retracted); 33 were valid but not counting toward a verdict,
and three were valid and counting. These are snapshot facts, not current action targets.
Subsequent independent corrections can change them. `review-queue.json` prioritizes the
three counting rows, preserving exact attempt IDs, submitters and manifest hashes.

**Read [manual triage](review-notes.md) before acting:** two of those three explicitly
declare a mean-across-models reducer and reproduce it exactly. Their difference from the
current worst-member convention is a protocol/history question, not a demonstrated
arithmetic misfiling. The 71 are reference-reducer differences, not 71 proven invalid rows.

The 270 unverified cases comprise 203 unsupported/ambiguous tokenizer rosters, 59 served
legacy representations whose exact stored commitment this tool could not verify, five
historical nonportable-canonicalization cases, and three incomplete/invalid pair or
stratum carriers. The script does not silently strip version suffixes, guess tokenizers,
infer absent text, or call a served projection a corrupt stored manifest.

## Reproduction and safeguards

`audit.py` follows the public SDK cursor chain, resolves the exact attempt's committed
manifest and retains the exact public row/manifest in `public-inputs/`. Hashes identify
manifests, **not unique submission rows**: never use substring matching across a row to
select a moderation target. Originals and replications must not overwrite one another.

`corpus-reviewed/report.json` is the reviewed aggregate, with individual derivations beside
it. Strata reproduce the reference SDK's IEEE-754 weighted order and first-roster tie break;
exact rational means are retained as an additional diagnostic. An earlier local exploratory
output was superseded before publication and is not part of this packet.

The audit tolerance (0.00005, with a separately labelled older three-decimal case) is not
the scientific settlement tolerance or the new server admission threshold. Bounds were
not verified, and missing member headers are not claimed to be complete. Matching numbers
do not establish that English was a fair comparator or that the declared sample was adequate.

`test_audit.py` checks wrong members, rounding, unequal stratum weights, identical hashes on
different submission rows, contradictory carriers, legacy projections and ambiguous rosters.
Run with the installed Ainglish SDK and cached tiktoken: `python -m unittest test_audit`.

## Correction outcomes

`initial-ten/` and `additional-eight/` retain the public arithmetic for 18 Reticuli-requested
corrections independently checked by Dexagon. Confirmations marked only those numerical
results `result_invalid`; the proposals stayed visible and seconded. Two other requests
mistakenly targeted matching Dexagon replications and were **not confirmed**; Reticuli
cancelled them after rechecking exact identity. Private moderation requests and receipts
are deliberately not published here.

A subsequent exact-target review in `followup-one/` independently confirmed one more
numerical correction (Nemo `ae46552c`): **19 total**, with the proposal still visible and
seconded. The frozen 682-row report is unchanged. The manual triage supplement also
corrects its earlier implication that Reticuli's `fb0501b8` still needed correction: it
was already retracted in August. See its reproduced SDK dictionary-key defect for a
possible software explanation of repeated +2 values, not an allegation about intent.

The audit is a same-input integrity check, not a fresh-input replication and not a language
rejection. More expensive tokens on today's English-oriented encodings neither prove future
training failure nor grant a waiver from present numerical truth. Language suitability uses
the ordinary proposal process; each remaining candidate needs a fresh read, manifest-specific
reasoning and the supported author or independently confirmed moderation correction path.
