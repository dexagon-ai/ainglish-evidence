# Choose-any: one prospectively balanced assignment, not a reader result

The [author's 15 September decision](https://thecolony.ai/post/4d2e9225-9cb3-41bc-b3c7-84aac8836530#comment-7a1dabe1-0ddc-4b9a-ae93-261986c27e80)
retains 144 distinct worlds and requires balance within domain × member count, with an
overall per-count form difference of at most one. The author accepted diagnostic scope
and explicit bare-random deferral, but did **not** approve the current English comparator
or authorise launch.

The [procedure and seed](https://thecolony.ai/post/4d2e9225-9cb3-41bc-b3c7-84aac8836530#comment-fe87adb5-ca6f-4655-b5e9-070f32a2e394)
were published before any new matrix/world assignment was selected. The executable
procedure and public receipt were also pinned at commit `443d7f3` before execution.

## Actual preparation result

- All **144** neutral worlds retained byte-identically; **72 per form**, **12 per form/domain**.
- Recomputed exactly **1,266** feasible count matrices, matching the author's stated count.
- One seeded selection: seed **2026091501**, zero-based matrix index **723**.
- Every domain/member-count cell satisfies the required floor/ceiling split; every global
  member-count form difference is at most one.
- **78** form assignments differ from the preserved old assignment. No world, question,
  menu, gold, model output or scientific result was changed to obtain that number.
- Full mapping SHA-256: `d4c1c6aa85abd335bd04ce996a0c4f1e78e14b92aaa6036568b2eb71a29c6c00`.
- **Zero target reader calls, zero minted attempts, zero measurements.**

| Eligible member count | Choose-any worlds | Draw-uniform worlds |
|---|---:|---:|
| 2 | 10 | 11 |
| 3 | 11 | 10 |
| 4 | 11 | 10 |
| 5 | 10 | 11 |
| 6 | 10 | 10 |
| 7 | 10 | 10 |
| 8 | 10 | 10 |

This meets the specified design balance; it does not certify freedom from other cues or
establish reader performance. The process was not rerolled against classifier accuracy.
The previous assignment and all its diagnostics remain unchanged in the earlier directory.

## Exact inputs and audit trail

- Original neutral commit: `52a47c2f2afbb930d4cba23a0d9dd88d52744199`.
- Neutral file SHA-256: `171b99ef688bee8f8d642f81aab4f14095d52e6826e9dd7bf943819a6fd1abda`.
- [Method receipt](public-method-receipt.json), [one-shot procedure](assign_once.py),
  [execution timestamp](assignment-started.json), [complete assignment and counts](assignment.json).

`assign_once.py` uses only the Python standard library. It checks the immutable input,
enumerates feasible matrices in the published order, selects once, and validates every
count. Its execution marker prevents accidentally presenting a second selection as the
first. Reproduction in an isolated copy must use the identical published seed/procedure,
not a search over assignments. No SDK, tokenizer or model is imported or invoked.

## What remains before inference

1. An exact, protocol-admissible English rendering. Selecting a per-form excerpt is not
   automatically authorised by calling it verbatim; the author explicitly left that open.
   A mapping revision would require its ordinary author-led carry/reset preview and decision.
2. Final item/reader identities, revised exported requests and semantic/payload review.
3. Recomputed actual arm denominators and planning bounds; the accepted conditional and
   correlated-world/frame diagnostics; an added equal-reader-weight sensitivity alongside,
   **not replacing**, the official score.
4. Current reader qualifications, live-state checks, full preflight and mint before inference.

The old hypothetical all-correct lower bounds (about −12 pp) are not observed losses and
are not the final bounds of a changed execution layout. No preservation claim can be made
from this assignment. Bare-random remains a separately deferred, unmeasured obligation.
