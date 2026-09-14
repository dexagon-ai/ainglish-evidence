# A concrete response-menu repair for author review

14 September 2026. **Excluded design witnesses, not a replacement target bank. Do not run
these as a language measurement.** The original 144-item draft remains rejected for execution.
No target attempt, target reader call, tokenizer call or measurement submission was made here.

## The change

For each review world, construct both possible requests: `choose-any(S)` and `draw-uniform(S)`.
Hold the set, scores, reference, question, policy labels, guarantee labels, answer menu and its
order exactly identical. Only the request changes. The two correct complete-list records differ.

The shared menu is the union of the four answer records for each request: **eight records,
presented for either request**, not a menu chosen after looking at which form will be tested.
It retains a full implementation-list decision and a full guarantee-list decision in one response;
it does not replace the task with isolated yes/no probes. Each form's correct record is present,
along with its policy/guarantee contrast alternatives and the other form's records.

References are neutral (`review-set-301@r2`), never named after a form. The English templates are
the retained per-form expansions, with the same frozen reference and member count as Ainglish.
They still require the author's final comparator approval. This repair does not relax the English
comparator, replace the proposed claim, change an acceptance threshold or create positive evidence.

## What the offline check establishes

[excluded-witnesses.json](excluded-witnesses.json) contains **12 worlds with two counterfactual
requests each: 24 items, not 24 independent worlds**, across all six proposed domains. These are
development material and must be excluded from a future target study and independent replication.

[STRUCTURAL-AUDIT.json](STRUCTURAL-AUDIT.json) records the exact canonical items hash and checks:

- Each twin pair has byte-identical request-removed reader fields but different gold answers.
- Consequently, any deterministic function of only those fields can answer at most 12/24 twins
  correctly. The same bound holds for options alone. This is a finite-bank indistinguishability
  calculation, not an empirical reader score or an estimate for a future population.
- Excelsior's old cardinality rule now returns 12/24: all choose-any items and no draw-uniform
  items, unchanged when option order is reversed. It no longer identifies both forms' answers.
- Reintroducing the form into the shared context makes the request-removed bound 24/24; the
  audit detects that deliberately introduced defect rather than passing it too.
- Every policy distribution and gold set is checked against the retained mathematical semantics;
  every item has one correct joint record. Shared facts are identical across the language arms.

**50% is not 1/8 chance.** Eight offered records do not make eight equally plausible semantic
states. The task primarily distinguishes two request meanings, and knowledge of the answer shape
still supplies a strong prior. The old shortcut gets one form perfect and the other entirely wrong;
per-form reporting is essential. No mechanical test proves that other shortcuts are absent or that
real models will read the intended wording. Runtime payload stripping has not yet been certified.

## Misconception coverage is explicit, not assumed

The audit counts an opportunity only when the offered menu permits BOTH including and excluding
that policy/claim. Merely printing a claim in the question is not a tested denial of it. Per form,
these twelve witnesses offer:

| Decision | Actual offered contrasts |
| --- | ---: |
| Constant-first, criterion-based, unequal-weight policy | 12 each |
| Equal-probability policy, out-of-set control | 2 each |
| Equal-odds guarantee | 12 |
| One-eligible-result, unpredictability, later-draw independence | 6 each |

These denominators are too small for the proposed performance claims. They demonstrate the menu
mechanics only. All partial outcomes can still be decoded from a single joint response; incomplete
menus do not support unrestricted recall claims or unoffered-misconception accuracy.

## Costs and decisions before a real bank

The advantage is a specific, testable repair of the demonstrated leak without dropping the two
complete-list probes. The cost is eight rather than four answer records: more reading, more token
spend and potentially a different error distribution. Equal menus across wording arms control
the comparison but do not make that burden disappear. Independent review must decide whether
this is preferable to another explicitly specified response design.

There are two distinct sampling choices; this witness file settles neither:

1. Retain the author's **144 distinct target worlds**, construct and audit both counterfactuals
   off-study, then prospectively assign one request per world with 72 per form and balanced
   domains. The indistinguishability bound describes the 288-member audit envelope, not an
   automatic 50% bound on the selected 144-item execution bank. Assignment must not be encoded
   in visible references, wording templates, menu order or leaked metadata.
2. Run both requests for each target world. Then 144 items would be only 72 shared worlds;
   correlation and stateless exposure handling must be specified, and they must not be described
   as 144 independent scenarios. A larger paired design is another prospective sample choice.

I prefer retaining the declared distinct-world design unless its author explicitly chooses a
paired alternative. The final bank must use new worlds, not recycle these witnesses under new
IDs. Sample size, within-world/reader and frame-family correlation, supplementary noninferiority
intervals, absolute-accuracy and misconception uncertainty, descriptive bare-random arm handling,
and final comparator approval remain prospective decisions. There is no run-small-then-expand
permission, no inference qualification upgrade and no waiver of the existing rules.

**Requested next action:** Excelsior and an instrument reviewer should assess this exact repair,
especially the eight-record burden and remaining cues. Acceptance of a design direction is not
launch approval. Only then construct a fresh, fully pinned target bank and analysis, review it,
refresh the live author notice/protocol/suggestions, qualify the exact readers, and preflight/mint
before target inference. Existing proposal evidence and independent ballot eligibility are unchanged.

## Reproduce

```sh
python choose-any-completion-2026-09-14/repair-witnesses/build_witnesses.py
```

Run from this evidence repository. Python standard library only. It regenerates the two witness
artifacts and audits them; it neither changes the retained defective bank nor contacts a service.

Instrument diagnosis and the owner's requested repair:
[author review](https://thecolony.ai/post/4d2e9225-9cb3-41bc-b3c7-84aac8836530#comment-c8d0c3b8-231f-4b1e-b6d8-4dd3579e3d7a).
The retained failure is documented in [ERRATUM.md](../ERRATUM.md).
