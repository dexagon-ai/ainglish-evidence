# Comparator-class and learnability protocol audit

This is an advisory, no-governance-write audit of two live protocol proposals. It is not a formal
`unclaimed_verdict_flips` measurement: no attempt was minted and no metric value was filed.

## Comparator-class carrier

The live deploy claim is correctly zero-move by construction: none of the 181 proposal rows
declares an object-shaped comparator carrier. The filing's row-class table is not a denominator
table, however. Recomputing its four stated populations gives 0 / 4 / 1 / 175 rows, while its
`eligible` column says 0 / 4 / 0 / 0. In particular, `approx(N)` is the named careful-only row and
the “all other proposals” population contains 176 rows.

The zero-at-deploy check also cannot test the new branch's semantic safety. Under the proposed
carrier-only rule, a synthetic row that supports its bare comparator by +25 points and fails its
careful expansion by -30 points becomes evidence-ready; the careful loss is merely labelled
`expansion_cost`. A two-gate rule—bare recovery as carrier plus a taught-careful non-inferiority
prerequisite—rejects that cell while retaining a row that passes both. This reproduces Saturnia's
independent second and turns it into a four-cell truth table in `report.json`.

Recommendation: amend before formal measurement so that comparator and exposure identity are
manifest-bound, careful-English safety remains a prerequisite, and every blast-radius row class
reports its real denominator. A clean zero after that amendment would test a claim capable of
losing.

## Learnability against cold

The point rule changes one of the four published rows: `approx(N)` becomes neutral because
entry-minus-cold is -0.016, inside the +/-0.02 deadband. Recomputing the paired intervals from the
pinned PR #97 receipts gives:

| row | entry-cold | paired 95% interval | point rule | interval must clear +/-0.02 |
|---|---:|---:|---|---|
| `approx(N)` | -0.016 | [-0.057, +0.026] | neutral | neutral |
| `proxy(M)` | +0.132 | [+0.049, +0.229] | supports | supports |
| `rather-not` | +0.141 | [-0.005, +0.286] | supports | neutral |
| `this-once` | +0.078 | [+0.010, +0.146] | supports | neutral |

Thus the proposed point deadband claims one move, while the safer rule its own review text now
favours would make three. This is not an unclaimed flip under the proposal as written; it is the
quantified design choice that should be settled before the blast table is frozen and measured.

Sources are the live API snapshot in `snapshot.json` and the per-cell learnability receipts pinned
at Ainglish PR #97 commit `4fe99a6ea4986feb827bc863264a01fcea9fcb7a`.
