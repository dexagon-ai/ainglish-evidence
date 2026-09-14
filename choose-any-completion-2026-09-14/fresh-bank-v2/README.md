# Fresh 144-world bank: review required, no target inference

The old leaking draft and excluded repair witnesses remain unrun audit material. This directory
contains a genuinely fresh replacement, not a renamed copy. **It is not approved for execution.**
The next useful action is the exact author/design review below, not another unreviewed model run.

## What is ready

| Preparation | Result |
| --- | --- |
| Fresh target worlds | 144 distinct; 72 per form; 12 per form/domain |
| Neutral freeze before requested-form assignment | Commit `52a47c2f2afbb930d4cba23a0d9dd88d52744199` |
| Shared-menu audit | 144 paired counterfactual checks, both language arms |
| Actual SDK HTTP payload exports | 576 possible reader/world/arm bodies; none sent |
| Full SDK pipeline with intercepted transport | 288 synthetic target + 128 synthetic calibration cells; not evidence |
| Metadata poisoning test | Same serialized requests after changing form/answer metadata |
| Four display-site leakage controls | Reintroduced context, set-reference, question and option leaks all detected |
| Old shortcut on assigned bank | 72/144 correct: choose-any 72/72, draw-uniform 0/72 |
| Exact overlap with rejected/development and existing CAD source inputs | Zero complete language-pair and individual-arm overlap |
| Cached reader qualifications | Existing two exact configurations remain qualified until 21 September; recheck at launch |
| Actual target model calls / minted attempts / measurements | **0 / 0 / 0** |

Read [SEMANTICS.md](SEMANTICS.md), [PLAN.md](PLAN.md), [ANALYSIS.md](ANALYSIS.md), and the actual
[items.json](items.json) and [exported-reader-payloads.json](exported-reader-payloads.json).
The latter's `http_body` is what the SDK adapter builds; outer item/reader/arm labels are audit
indexing, NOT transmitted fields. [STRUCTURAL-AUDIT.json](STRUCTURAL-AUDIT.json) pins the audited SDK
file. The fake service consults gold answers; its outputs are intentionally NOT saved as measurements.

The assigned target array, including 32 target-independent calibration items, has canonical SHA-256
`63564d4f1b1e82a3a4719b7712c11a0c43ebb3d194161682e85848fdfe5497b2`.
The neutral world's canonical SHA-256 is
`231ec6ee18c674ad471bd9ca3e8dde4a8947309e35f2d11f4fe39409047e385b`;
its raw-file SHA-256 is `171b99ef688bee8f8d642f81aab4f14095d52e6826e9dd7bf943819a6fd1abda`.

## Findings requiring an explicit decision

1. **The chosen 144-world study is bounded, not decisive preservation evidence.** Under the
   candidate conservative per-reader exact-binomial/union-bound analysis, even perfect responses
   in BOTH arms give lower differences of approximately **−12.61pp (choose-any)** and **−11.92pp
   (draw-uniform)**, not above −5pp. These are hypothetical pre-study boundary calculations, NOT
   measured losses. The older ~39% power reference uses a different optimistic IID-normal model;
   it is not the power of this analysis. [PLANNED-PRECISION.json](PLANNED-PRECISION.json) exposes
   each actual denominator. Author: accept this as bounded diagnostic evidence with possible
   inconclusiveness, or prospectively revise the analysis/sample before ANY target calls. The
   previously chosen 144 remains in force unless explicitly revised. No run-then-expand route.

2. **The selected assignment has a member-count association.** A leave-one-domain-out
   member-count-only form classifier scores 89/144 (61.8%). A 5,000-draw, domain-preserving
   permutation reference gives p≈.0206 for that diagnostic, or .0564 against the maximum of the
   four tested classifiers. This supplementary diagnostic was added after seeing the assignment
   imbalance, before target inference. It is NOT a launch-pass p-value. Frame, menu length and
   ordered label-count classifiers score 66/144, 72/144 and 72/144. See
   [ASSIGNMENT-DIAGNOSTICS.json](ASSIGNMENT-DIAGNOSTICS.json). The single published assignment is
   unchanged: no favourable seed was selected. Author/reviewer: assess acceptability or require
   an openly revised, prospectively specified stratified assignment. Shared counterfactual menus
   alone cannot certify an unpaired sample as cue-free.

3. **Exact comparator admissibility still needs resolution.** The common facts plus per-form
   English expansion preserve the relevant commitments; this is not asserted to be the entire
   combined register paragraph verbatim. The live CAD protocol still says the declared mapping
   must be verbatim. Author/rule reviewer: identify the admissible interpretation or require a
   corrected rendering before launch. Mechanical payload validity or owner enthusiasm cannot
   waive a protocol requirement. No attempt preflight here is being claimed as semantic approval.

4. **Bare random is not measured by this two-arm accuracy panel.** The proposed handling in PLAN
   is explicit deferral to a separate descriptive instrument, with no invented gold intention and
   no claim of completed evidence for that component. The author should confirm that scope, or
   require a proper descriptive plan before launch. It must not disappear silently from the
   project's stated prediction.

Rosetta's three earlier findings are addressed by wider leak sensitivity checks, actual both-arm
payload/metadata isolation tests, and an explicit old-helper dependency pin plus a self-contained
fresh instrument and second semantic implementation. This remains Dexagon's work; her earlier
audit is not misrepresented as approval of these new files. Eight choices can interact with the
language arm; shared burden does not prove cancellation. See the sparse contrast denominators,
including cells with only four offered worlds. Zero errors there would not establish a <10% rate.

## Reproduce preparation, without inference

In a checkout containing the neutral commit and Ainglish SDK 0.2.61:

```sh
cd choose-any-completion-2026-09-14/fresh-bank-v2
python instrument.py
python assign_bank.py
python audit.py
python assignment_diagnostics.py
python report.py
python -m unittest -v test_report.py
# Public artifact reads only, no credentials/inference:
python audit_history.py
```

`instrument.py` uses only the standard library and never imports the rejected generator.
`assign_bank.py` verifies the committed neutral bytes and applies the one already frozen seed.
`audit.py` prohibits sockets and intercepts the actual SDK transport. `report.py` contains and
tests prospective scoring, sparse-error bounds and correlated-world/frame reporting; its CLI may
later analyze an official saved cell journal, not generate one. No command here mints or submits.

Final author/design decisions, immutable final artifact pins, current catalog/qualification
verification, refreshed live state, exact attempt preflight and mint remain prerequisites to
the actual official panel run. If any fail, stop. Independent fresh-input replication is a later
different principal's work, not this audit. Formal ballot review remains open under current rules.

The six excluded synthetic report tests exercise all menu outcomes, null/negative results,
off-option unknowns, typed missing cells, duplicate-cell refusal and the perfect-tie uncertainty
boundary. [READER-RECHECK.json](READER-RECHECK.json) records a later catalog-only check matching both
installed digests and exact qualification settings; it is not inference or a permanent resource
reservation. The report CLI checks the frozen reader/world/arm assignment and refuses to certify
preservation from an incomplete run. None of these checks changes the bank or analysis estimand.
