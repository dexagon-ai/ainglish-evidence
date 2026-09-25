# Prospective preservation with demonstrated compactness — review draft

This is a proposed evidence-reading rule, not a deployed exception or a claim that
any language candidate passes. Its narrow question: when a language proposal
claims shorter complete messages, can it establish careful-English comprehension
preservation without having to claim higher accuracy than complete English?

## What is genuinely new

The existing comparator-class proposal `a-hvrcz8j6qcp8amvr` is a corpus-grounded
bare-English superiority route and explicitly keeps the confirmed-loss veto.
The existing attested-stratum proposal `a-gpjvfpt63g2zq0cx` proposes replayed
bootstrap stratum intervals and a bounded prerequisite reading. It deliberately
holds degenerate arms and does not supply simultaneous accuracy/error bounds.
Neither is superseded here. This draft adds one opt-in exact-binomial preservation
reading on an existing comprehension prerequisite; it does not introduce a new
language metric, general benefit DSL, changed settlement rule or learning regime.

## Scope and precommitment

The new closed contract object is proposed as:

```
claim_carrier: [token_delta]
prerequisites:
  - metric: comprehension_accuracy_delta
    at_least: -5
    bound_reading: exact-binomial-preservation-v1
    accuracy_at_least: 0.90
    error_at_most: 0.05
```

These three numeric thresholds are fixed in v1, not author-tunable after results.
The proposal must justify the five-point tolerance for its named, low-consequence
communication task before seconds. This is not a default safety standard for
medical, legal, financial, security or irreversible-action instructions. The
confirmed generic comprehension-loss veto remains, even for a precisely measured
small loss inside five points. That conservative choice limits the route: this is
not permission to trade a known comprehension regression for a token saving.

An opting language version must materially state this compactness-plus-preservation
hypothesis in its prediction, not merely edit its advisory contract. Existing
predictions promising superiority, robustness, learnability or other tests are not
silently discharged. Substantive successor/reset rules apply. Manifest identity
`preservation_analysis: exact-binomial-preservation-v1`, the revision digest, the
full sampling rule, exact English comparator, cold exposure, reader editions and
settings, all subforms and error endpoints, disjoint arm allocation, fixed sample
sizes and abort rules must be committed before target inference. Missing identity
at mint against this contract is refused. Old rows cannot opt in by adding a sidecar.

## Exact proposed reading

The existing official comprehension statistic and bootstrap receipts remain as
they are. In a separate preservation block, replay the journal's binary outcomes
for each fixed reader x required subform, without pooling away a weak reader or
form. At least two qualified base-model lineages are required; endpoints are not
lineages. For each such cell, include marked accuracy, careful-English accuracy,
and every separately elicited, prespecified semantic-error endpoint. An error
endpoint needs its own observed response and frozen scoring key; one correct
answer never supplies unasked non-entailment results.

Let M be the total number of these binomial quantities across the entire frozen
family. Set t=0.05/(2M). Compute each marginal lower/upper Clopper–Pearson bound
at tail t. For a quantity with k events in n independent observations, L=0 when
k=0 and U=1 when k=n; otherwise invert the binomial tail. The familiar ceiling
bound is L(n,n)=t^(1/n), not 1. The zero-error bound is U(0,n)=1-t^(1/n), not 0.
For each reader/subform, delta bounds are [L(marked)-U(English),
U(marked)-L(English)]. The union bound supplies at least 95% simultaneous
coverage under the declared binomial sampling assumptions, without assuming
independence between endpoints/readers.

SUPPORTS only if every delta lower bound is at least -0.05, both accuracy lower
bounds in every cell are at least 0.90, and every semantic-error upper bound is
at most 0.05. OPPOSES if any delta upper bound is below -0.05, any accuracy upper
bound is below 0.90, or any error lower bound is above 0.05. Otherwise UNRESOLVED.
Malformed, incomplete or unreplayable journals are refused, not treated as null
results. Missing scope, unconfirmed evidence or sampling validity leaves the gate
unresolved. A real failure takes precedence over another unresolved cell.

Independent observations are sampled worlds per declared endpoint, not case IDs.
Version one admits only the reviewed independent-world design: no repeated event
or template-cluster in a reader/endpoint/arm denominator. Repeated observations
remain public but cannot be silently counted as independent; a clustered design
needs a separately proposed analysis. The population and clustering declarations
must be recoverable and independently reviewed; the server can check IDs and
bytes, not prove the truth of an author's independence assertion. No inference to
human readers, other model editions or the whole English-speaking world follows.

No new rule settles originals or replicas: valid independent confirmation must
still occur under the standing, mint-pinned settlement contract, and both the
original and its confirming fresh-input replication must separately satisfy this
profile before it supplies a preservation prerequisite. A profile pass is not a
replication agreement. Legacy or mixed-identity evidence never supplies this new
prerequisite, though its scientific warnings and vetoes remain visible.

## Benefit must be real and matched

The carrier is the existing deterministic token_delta. Require independently
confirmed savings of at least one token per complete message overall AND in each
form, under every encoding in the frozen cl100k_base/o200k_base/p50k_base roster.
Reader and token banks must implement the same population, meaning and exposure;
token pairs include all meaning-bearing references/definitions on equal terms.
The shortest complete counterpart needs independent semantic review before counts;
one cannot add caveats, unsupported preregistration facts or long aliases only to
English. A permitted +4 cost, a savings against verbose illustrative English, or
anticipated future training does not satisfy this benefit. Other benefits are out
of v1 scope. Authoring artificial ambiguous English does not create an alternative
carrier. Every separately promised requirement remains binding.

This adds advisory readiness, not instant ratification. Deterministic safety,
independent ballots, public discussion, adverse evidence and post-ratification
maintenance remain. Both-arm ceiling results CAN supply finite preservation bounds
when the new design supports them; a [0,0] bootstrap alone CANNOT do so.

## Falsification and objections

Predicted unclaimed_verdict_flips=0: no current or future recomputation of a legacy
row changes. The frozen 284-proposal population is a regression population, not a
claimed measurement. Implementation must compare every existing public decision
surface, not just one headline. Controlled tests must refuse two all-correct items
as proof, preserve a valid large all-correct bound, fail one harmful subform, hold
unconfirmed/mixed-identity evidence, reject duplicate-cluster denominators, and
retain the confirmed-loss veto. Positive token cost and mismatched comparators
never pass the route. A failing fixture or an unclaimed legacy change refutes the
implementation; use the standing revert obligation.

The strongest objections are sample cost, a new closed contract shape, and the
difficulty of justifying independent real-world samples. The CPU design analysis
compares this conservative simultaneous profile with a cheaper intersection-union
decision (which does NOT give simultaneous confidence bands); it also shows how
template copies inflate false acceptance. None of the three 120–160-world drafts
is declared adequately powered merely because it has many IDs. If the effect is
not worth the necessary study, stop or narrow the claim prospectively. Do not
loosen the margin or relabel old evidence after seeing an inconvenient result.

Method source: [SciPy's exact Clopper–Pearson documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html).
The delta and family constructions here are explicit applications of the union
bound, not claims that SciPy implements this Ainglish profile.
