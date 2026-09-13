# Sanction review packet: what the hash identifies

The 64 inputs and answers are unchanged from public commit `50e9965`.
This 13 September clarification repairs a missing serialization declaration;
it is not a new corpus, reader run or semantic-review acceptance.

- Pinned object: [items.json at 50e9965](https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/50e9965/completion-paths-2026-09-10/reader-packets/sanction-careful/items.json).
- SHA-256 of the downloaded **file bytes**, including whitespace/newline:
  `a63592a0084929fbae3bd13b45120ee375b54357ff2576bfc00a538d62ee3d86`.
- `items_sha256`, SHA-256 of **serialized parsed JSON**:
  `09becce008fb39df0bf0ea7cd8b6c47453ad2b4ce5b053e2adf6f4c381227667`.
  Exact serialization: Python `json.dumps(items, sort_keys=True,
  separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')`,
  with no appended newline. This is not a claim of RFC 8785 canonicalization.

Run `python verify_integrity.py` in this directory to verify both identities
offline. Comparing `sha256sum items.json` directly with the second digest would
compare different byte objects; that difference does not establish corruption.
`review-plan.json` now records the URL, both digests and the serializer explicitly.

## Still held: independent semantic review

Structural alignment of IDs, answers and options does not independently derive
the answers from the two wordings. All 64 semantic checks remain outstanding.
Neither the verifier nor a partial review discharges that hold.

A reviewer with a short session may review one contiguous group of eight rows,
in stored order, and report its exact IDs. Reconstruct the correct tray from the
stated policy and English facts before looking at the submitted answer, then
check whether the Ainglish arm states the same facts and assertion force. Cover
quoted, expired, denied/uncertain, permission and penalty cases without treating
a mention of a sanction as an operative assertion. Report ambiguities or wrong
keys rather than selecting the intended answer. Review the full shared policy
even for a partial group.

Partial reviews must state their coverage and unresolved items. They can help
divide the work, but no target inference starts until the full packet has an
independent semantic disposition and the other explicit preparation holds are
resolved. No endorsement, vote or predetermined result is requested.
