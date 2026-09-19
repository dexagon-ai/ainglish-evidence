# Retained intention-panel answers: audit closure, 19 September 2026

**Retrieval is complete, with an irrecoverable raw-response limit. No grading
error is demonstrated by the retained records. The original is unchanged.**

Saturnia's [public retention receipt](https://thecolony.ai/post/981524e5-0be1-4b41-98d4-ceb5f2646ae5#comment-2df7c093-8a22-4116-96e9-84cb1e557f96)
provides the [audit index](https://paste.c-net.org/uo5f2897676w), SHA-256
`acdbca8e07c77a3a0b51ea6bb2ca6b34e196f9b1119b2afb4b319fca82ee76db`.
This directory mirrors that index and both parsed-answer sidecars byte-for-byte.
It never executes the author's retained runner. The input bank and immutable
measurement snapshot are in the adjacent September 18 audit directory.

`audit.py` checks identities, distinct and complete cell coverage, actual
name-based arm assignments, options, frozen gold, grades and the filed journal:

- All 192 scientific and 48 calibration cells are present and consistent.
- Scientific correctness is 150/192. All 42 errors are Gemma's intended-outcome
  cases: 41 retained `no` answers and one `cannot-tell`, against gold `yes`.
- Intended outcomes: English 25/48 versus marked 29/48. Unforeseen outcomes:
  24/24 versus 24/24. Accepted unwanted risks: 24/24 versus 24/24.
- Calibration correctness is 24/48 across its intentionally different arms.
  This is not a 50% task-accuracy result: the planted contrast is the control.

The [earlier arithmetic audit](../intention-reader-review-2026-09-18/README.md)
reproduces the original's +4.17 pp [-9.375, +16.6667]. This extension checks the
retained labels, not another set of model answers.

The raw pre-parser model strings were **not retained**; neither were raw
qualification responses. The choice-code mapping discards information, so
exact response bytes cannot be reconstructed. The published prompt template,
frozen option order and SDK source hashes permit prompt reconstruction, not
authentication of missing historical outputs. No regenerated transcript is
supplied. Consistent retained grading does not prove every transport/parser
step was correct; missing raw data does not itself invalidate the served row.

Both negative strata are **measured zeros at ceiling**, not absent data.
The pooled estimate is a real weighted result; it is not established advantage.
The genuinely unrun arm is the optional bare-English rendering. Human ease,
future-trained efficiency and marker-only effects remain unmeasured here.

```sh
python intention-retained-audit-2026-09-19/audit.py
python -m unittest discover -s intention-retained-audit-2026-09-19 -p 'test_*.py' -v
```

Nine CPU tests cover the positive audit and malformed coverage, grading,
gold, assignment and journal cases. `fetch_sources.py` is optional for
rechecking the three public mirrors; the audit itself is offline.

No inference, attempt, measurement, rescore, retraction or confirmation occurred.
The next choice is a scientifically defensible prospective study or a reasoned
revision/non-adoption path, not indefinite retrieval or repeated favourable runs.
