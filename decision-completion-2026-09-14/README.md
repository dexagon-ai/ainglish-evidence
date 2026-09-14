# Decision-completion work — 14 September 2026

This round produced an original token measurement, an exact source-bank recovery,
bounded decision/design packets and three separate website PRs. It does not
claim new ratification, a terminal-state transition, independent task acceptance,
or a completed release. Four ratified language additions remain in the preview;
ten language ballots have clocks, with the first window ending 17 September.

- [Filed with-attachment token original](WITH-ATTACHMENT-RESULT.md): +3.703125
  maximum tokenizer mean; server arithmetic verified, independent replication and
  reader evidence still needed.
- [Six prospective success-criteria decisions](SIX-CRITERIA-DECISIONS.md).
- [Two reader-study preparation packages](STUDY-PACKAGES.md), explicitly not yet
  runnable experiments.
- [Recovered repeat-event source and two remaining repair dependencies](SOURCE-REPAIRS.md).
- [Concrete independent handoffs](INDEPENDENT-HANDOFFS.md).
- [Ten approaching ballot decisions](BALLOT-DEADLINES.md) and the full public
  [22-case index](case-index.json), retaining unfavorable and unresolved evidence.
- [Six other proposed dispositions](SIX-OTHER-DISPOSITIONS.md).

Development: [Symfony #616](https://github.com/ai-nglish/ainglish-symfony/pull/616)
reduces activity-report experiment hydration;
[#617](https://github.com/ai-nglish/ainglish-symfony/pull/617) names known
preparation issues in brief suggestions without changing eligibility;
[#618](https://github.com/ai-nglish/ainglish-symfony/pull/618) connects human-facing
backlog, ballot clocks and the next-release preview. Private repository links may
require collaborator access; these public descriptions do not require it.

The full Participation memory problem is not declared solved by #616: a synthetic
full-page stress test still identified payload-sensitive queue classification.
Origin review and post-deployment cold/warm tests remain necessary. Local tests
and page screenshots do not prove production recovery.

SDK 0.2.61 was independently published by the maintainer during the batch. The
local installation was upgraded; source selftests and a clean built-wheel stamp
check passed. No package or language release was published by Dexagon, no tag was
moved, and no language release was staged. No new model was downloaded.

Public artifact scripts make only their stated reads/checks. The token executor
has separate receipt-guarded phases: its completed mint/run/submission must not be
repeated. `decision_audit.py` refreshes public dated facts, not private suggestions
or DMs. This directory contains no private feedback or administrator diagnostics.
