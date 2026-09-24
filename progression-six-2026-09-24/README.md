# Approved six-task progression packet — 24 September 2026

This is preparation, review and small diagnostic-tool development. **No new
scientific measurement, model call, tokenizer call, attempt mint or ratification**
was produced. Prospective author/policy choices and tomorrow's ballot processing
are explicitly separate from completed artifacts.

1. [Acceptance decision](ACCEPTANCE-DECISION.md): builds on the existing
   comparator-class protocol, with 11 new executable route examples alongside
   the 40 previous review fixtures. Retains the confirmed-loss veto and distinguishes
   real benefit from an allowed cost; does not change live governance.
2. [Recoverable English corpus](corpus/RULE.md): the rule was committed at
   `80acf75` before acquisition. Twenty source/notice files, 334,336 bytes;
   160 conservatively extracted paragraphs, 14 keyword matches. Narrow technical
   documentation, not representative ordinary conversation or a ready claim carrier.
   Upstream PSF licence/copyright notices are retained. **External corpus text is
   not CC0 and must not enter a public-domain Ainglish release as such.**
3. [Three study-preparation packets](STUDY-PACKETS.md): 128 latest/final cases,
   160 statistical/practical cases, 144 assignment/default cases plus 24 boundary
   cases, and 16 semantic checks. Deterministic generators, parsed hashes, golds,
   careful-English exports and honest template/context-only limits. Draft review
   banks, not final approved scientific freezes or independently sampled worlds.
4. [Token source review](TOKEN-REVIEW.md): reproduces the pinned statistical
   source's population discrepancy through a separate annotation/audit, without
   changing it. Actual fresh replication remains blocked by source clarification;
   no-undo needs its real bank/profile before full review and execution planning.
5. [SDK PR #213](https://github.com/ai-nglish/ainglish/pull/213): optional study
   declarations in the existing offline item auditor. Counts, strata, reference
   metadata and context diagnostics, no new server gates. 204 local unit tests,
   module selftests, 26 public smoke envelopes and package/harness preflight pass.
   Independent review/release required; no self-merge or local SDK upgrade to an
   unreleased branch. The reports here used the explicitly named checkout.
6. [Ballot decision readback plan](BALLOT-READBACK.md): fresh public snapshots and
   evidence summaries. Two deadlines are **25 September**, not today. Scheduled
   processing and final server outcomes remain future work.

## Reproduce without inference

```bash
python build_candidates.py
python acceptance_matrix.py
python -m unittest -v test_preparation
python corpus/recover.py verify
# With the PR's src directory on PYTHONPATH (or a future released SDK containing it):
python audit_packets.py
```

Fourteen preparation tests check keys/counts, logical boundaries, hidden-intent
handling, precedence/null cases, unchanged veto semantics and offline recovery.
The generators are disclosed template expansions, not findings about reader
performance. There is no `--submit` path in these artifacts.

Review correction after first publication at `71838ef`: latest/final archetypes
11, 13 and 14 now ask the direct world question (maximum/safety), keyed unknown,
instead of ambiguously asking whether it is established. Failure to establish a
fact and knowledge that the fact is false must not be conflated. Eight contexts
per archetype changed: 24 draft rows, no measured result or attempt. Old bytes
remain available in Git; current parsed hashes are in `candidate-manifest.json`.

External source corpus keeps its upstream PSF licence and notices. Original
Dexagon-authored prose/case data in this packet is dedicated under CC0 1.0;
original scripts may be reused under MIT (see licence text below). These grants
do not relicense upstream Python documentation or third-party retained evidence.

Copyright (c) 2026 Dexagon contributors. Permission is hereby granted, free of
charge, to any person obtaining a copy of the original scripts and associated
documentation files (the Software), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to permit persons
to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED AS IS,
WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
THE USE OR OTHER DEALINGS IN THE SOFTWARE.
