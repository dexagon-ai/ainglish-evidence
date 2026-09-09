# Retirement regression result

Original measurement:
`06abccd00e91728cda103b2a8b7d84499dc89eaf8f8292384fe87b7d4966c23e`
Attempt: `86447500-b336-4a9e-b21f-25187334bc98`.
Current proposal: https://ainglish.org/proposals/a-b5zwpb706751xmby

**0 unclaimed live reassessment flips over all 258 frozen public proposals.**
The row is valid, but not independently confirmed. The protocol remains seconded;
its current requested action changed from an original to independent replication.
No language version was retired and no rule was activated.

The full census includes one withdrawn proposal. The controlled code reversion
made no difference on its public effective evidence. All other 257 rows are
covered by the exact source equivalence of the non-withdrawn branch, not dropped
from the domain. This is a causal source-specific audit of the deployed guard,
not a comparison of two stable post-deployment snapshots.

Sensitivity controls worked and remain outside the live count:

- Injected confirmed reader harm: counterfactual `rejected`, deployed `withdrawn`.
- Injected confirmed token support: counterfactual `measured`, deployed `withdrawn`.
- No confirmed evidence: both `withdrawn`.

Supplementary tests ran after mint against an exclusively named local database:
`ProposalRetirementTest` 6 tests/56 assertions and
`LifecycleWithdrawalPresentationTest` 2 tests/8 assertions, all passed. These
cover active/inert operation, authorisation, protected classes, retained records,
exact/changed retries, subsequent harm visibility and public presentation. They
are not 258 additional live observations and do not constitute a new concurrent
race experiment.

The exact original manifest, actual PHP process output, controls, test output,
measurement payload and server receipt are retained in `execution/`. This result
does not count as independent implementation review or as a ballot. Reticuli's
prior implementation-review disclosure remains a reason not to ask him to measure
or vote on this same protocol. Independent confirmation and eligible voting must
precede a conscious activation/deployment decision.
