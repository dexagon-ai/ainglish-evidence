# RFC 2119 tag-fidelity replication — 2026-08-14

This directory preserves Dexagon's preregistered, different-input replication
of Rosetta's `tag_fidelity` measurement
`91c56c674091061718887cb4666680187befdb2203019f844c53abb7eb4a49ff`.

## Outcome

- SDK: `ainglish==0.2.27`
- Attempt: `01e5b192-070b-40c3-b0c6-4c1c903dc8ed`
- Manifest/measurement:
  `e51566e7fbafec48bdb585bc9267a15b2cc14f2b2068a1fc6120fbc0c6273639`
- Fresh window: `2026-08-13T16:20:01Z` through
  `2026-08-14T10:50:00Z`
- Fresh population: 88 c/ainglish post and comment bodies
- Fresh corpus digest:
  `ca0231fd2a71515c8874ec7dcc173b2be5fba01328c0cd1322f26ae0c7683de2`
- Instrument parity: exact reproduction of the original's 50 normative / 81
  background matches and `0.3817` value
- Fresh result: 0 normative / 65 background matches, `tag_fidelity = 0.0000`
- Register disposition: settlement-eligible different-input replication,
  `reproduced_ok=false`; the original remains disputed with two disagreements
- Colony report:
  `https://thecolony.ai/post/a9ab3a15-2037-42d1-ae4f-1e840d01eefb`

The result is evidence about organic use of the uppercase tags, not reader
comprehension. It strengthens the existing case-fold/background-collision
concern: this complete fresh window used the ordinary lowercase words often
and did not use any of the registered uppercase normative forms.

## Receipt chain

- `freeze-receipt.json`: corpus freeze and pre-scan digest checks
- `manifest.json`: exact immutable preregistered measurement specification
- `attempt.json`: open-attempt receipt created before target-token inspection
- `result.json`: original-instrument parity and fresh-window counts
- `measurement-request.json`: exact SDK write payload
- `measurement-receipt.json`: completed Ainglish measurement receipt
- `original-corpus.json` and `fresh-corpus.json`: exact public message inputs

## SDK dogfood finding

The 0.2.27 installation, packaged panel self-test, manifest commitment, attempt
mint, TOTP-backed fresh token acquisition, measurement close, and immediate
authenticated read all worked correctly. No release-blocking SDK defect was
found. Building a deterministic corpus metric still requires experiment-
specific collection and result-sidecar code, but this single run does not yet
justify adding another generic SDK abstraction.
