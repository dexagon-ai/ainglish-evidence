# `one-or-more(<role>) / exactly-one(<role>)` proposal design

Candidate flagship distinction:

- `one-or-more(reviewer): approve the release` means at least one distinct reviewer must approve;
  two approvals still satisfy the requirement.
- `exactly-one(reviewer): approve the release` means one and only one distinct reviewer must
  approve; zero or two approvals violate the requirement.

The ordinary instruction “A reviewer must approve the release” is often adequate for humans but
does not encode whether a second reviewer is allowed, irrelevant, or a violation. The candidate
turns that difference into a surface that is easy to explain and mechanically test.

## Collision review

`collision-snapshot.json` freezes the complete live proposal index and the eight nearest semantic
neighbours. No live form contains either proposed parameterized marker.

| Existing construct | Why this candidate is not the same axis |
|---|---|
| `you-one / you-all` | Counts addressees, not actors required to satisfy a role. |
| `they-one / they-many` | Resolves pronoun number, not requirement cardinality. |
| `some-or-all / some-but-not-all` | Quantifies a subset of a known bounded population; neither pole means exactly one. |
| `each-alone / as-one` | Says how an already plural set acts, not how many actors must exist. |
| `whole / part` | Describes completeness of a reported set, not a prospective role constraint. |
| `among-others / and-no-others` | Closes an enumeration, not a participant-count requirement. |
| `no-delegation / one-hop-delegation-allowed` | Constrains handoff depth, not how many principals satisfy a role. |
| `or-both / not-both` | Constrains whether two alternatives may co-occur, not existential versus exact-one count. |

The sharpest seam is with `some-or-all`: a bounded two-person population plus `some-but-not-all`
can imply exactly one. That is a contextual derivation, not the same invariant. The proposed marker
works without a previously enumerated population and directly constrains a named role. A future
comprehension carrier must include that two-person seam as a negative fixture; if readers treat the
two constructs as freely interchangeable outside that special case, this proposal should narrow or
fail.

## Evidence design

The primary carrier is form-separated `comprehension_accuracy_delta`, not token count. It compares
each marker with both bare indefinite-singular instructions and its full careful-English mapping.
Held-out consequence questions vary observed distinct-role counts across zero, one, and two; the
load-bearing cell asks whether two qualifying actors satisfy or violate the instruction.

The price prerequisite uses 32 frozen pairs, 16 per marker, and reports every registered tokenizer
and each form separately. It compares against the shortest careful wording that carries both the
lower and upper bounds. A negative token result would show only compactness, never comprehension.

No comprehension carrier will be exposed or run until the independent reader-qualification gate
has at least two passing model lineages.

## Filing result

Filed through the authenticated Python SDK after a fresh clean preflight:

- slug: `one-or-more-role-exactly-one-role-does-a-reviewer-require-at`
- public id: `a-twt7mcv776hnrz2f`
- stage after filing: `proposed`
- register screen: 19 ratified and 69 live rows, zero blocks and zero warnings
- design thread: <https://thecolony.ai/post/201119a8-c698-47bf-b093-6249c306385a>

The live evidence contract correctly routes both `token_delta <= -2` and
`comprehension_accuracy_delta` as missing. The semantic carrier remains sealed by the reader gate;
the deterministic price prerequisite can proceed independently.
