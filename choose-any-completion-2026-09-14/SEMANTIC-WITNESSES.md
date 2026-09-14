# Meaning checks for reviewers

These are public design witnesses, **excluded from the experimental item bank**. They are derived
from the live mapping, not reader measurements. The author/reviewer should correct any wrong
entailment before a final study is frozen.

| Situation | choose-any | draw-uniform | Why |
| --- | --- | --- | --- |
| S = {A, B, C}; always return A | Allowed | Not compliant | Every identity is acceptable in the first request; probabilities 1,0,0 do not meet the second. |
| S = {A, B, C}; always return the least-loaded member | Allowed | Not compliant | An unconstrained criterion is permitted, but it is not equal-probability sampling. |
| S = {A, B, C}; probabilities 1/2, 1/4, 1/4 | Allowed | Not compliant | Unequal weights still return exactly one eligible identity. |
| S = {A, B, C}; probabilities 1/3 each | Allowed | Compliant | choose-any permits uniform sampling; it does not prohibit randomness. |
| Always return D, with D outside S | Not compliant | Not compliant | Exactly one result is insufficient when it is ineligible. |
| Return two distinct members | Not compliant | Not compliant | Both forms specify one member, not a sample of several. |
| Two rows name A and one row names B; sample rows equally | Allowed if exactly one eligible identity results | Not compliant for the identity set {A,B} | Duplicate rows cannot buy an identity extra probability. |
| S contains just A; always return A | Allowed | Meets the one-member distribution | The mapping allows this degenerate case. The proposed study deliberately uses 2–8 members to test a real distinction. |
| S is empty | Invalid request | Invalid request | Neither instruction licenses choosing outside the set or guessing a fallback. |
| S changes concurrently and no version/time resolves it | Invalid request | Invalid request | There is no frozen, uniquely resolved eligibility set for the request. |
| The only observed outcome is A | Consistent with compliance, if membership and cardinality are established | Distribution still unknown | One realised outcome does not establish equal probabilities or establish their absence. |
| A draw is uniform, but no security or later-draw contract is supplied | No extra promise | No extra promise | Neither term adds cryptographic unpredictability, cross-draw independence, replacement policy or a balanced finite sequence. |

The last two distinctions must not be collapsed into a binary “randomness verified” label. The
study evaluates readers' understanding of an explicitly stated procedure, not the empirical
quality of a real random-number generator.
