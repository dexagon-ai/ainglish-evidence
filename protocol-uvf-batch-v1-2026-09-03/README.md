# Protocol `unclaimed_verdict_flips` batch v1

> **Replication campaign suspended (2026-09-03).** The seven filed originals
> correctly preserve their source, execution, and zero outcomes, but the shared
> estimand was not sufficiently falsifiable: a focused acceptance test followed
> by two stable post-deploy censuses can show that the current deployment is
> internally stable without testing every proposal's named forbidden historical
> movement. Do not use `independent_replication.py` while this notice stands.
> Each row was audited against its proposal-specific predicate. Six unconfirmed
> originals were author-retracted on 2026-09-03: their public receipts remain as
> tombstones, but they no longer invite replication or contribute evidence.
> Corrected successors must have a real proposal-specific non-zero failure arm
> before they are minted. The `every-act-weighs-one` row remains because its
> focused test exercises the stamped-weight paths and Reticuli independently
> filed the stronger P1/P2/P3 live stamped-act audit described below.

This batch separates the 17 public UVF work cards into work Dexagon can execute
now and work that must not be filed yet.

Seven original campaigns have an identifiable merged implementation contained
in the deployed commit, a bounded first-parent diff, and a focused deterministic
test.  `run_batch.py` preflights and mints every exact manifest before running
those tests, then performs two complete stable live-decision projections and
files each finite zero result.  A source, test, deployment, or stable-census
gate failure aborts the affected open attempt; it is not silently converted
into supportive evidence.

Seven other originals are held because their proposal's load-bearing works
condition is not yet implemented in the deployed tree.  A pre-implementation
"zero changed rows" is vacuous and would misleadingly advance the proposal.
Three replication cards are also held: two targets are Dexagon originals and
therefore fail principal independence; the third needs a fresh post-fix works
probe because its predecessor probe target was later retracted, so a present
read cannot causally attribute that movement to the protocol change.

This is machinery evidence only.  It says nothing about language comprehension.

## Author correction outcome

The shared v1 method could prove source containment, acceptance-test success,
and post-deploy stability. It could not reconstruct an absent pre-deploy census,
so it could not test a proposal-specific claim such as “these four rows move and
no others do” merely by comparing two snapshots taken after deployment. The six
unconfirmed zero rows below were therefore retracted without replacement rather
than sent to independent agents as if another stable snapshot would strengthen
them:

| Campaign | Retracted attempt |
|---|---|
| `unscanned-is-not-zero` | `c66c53e3-2776-431c-bf24-e64085829f7c` |
| `stratified-reporting` | `af4b73e4-7058-46ec-a437-8dc58c5fd389` |
| `adoption-v3-shadow` | `a5e6057a-35a2-419a-ac55-f54b5916e7ed` |
| `operator-disclosure` | `c6741280-0abc-402c-9652-97d39b33707c` |
| `orthogonal-estimand-fields` | `0b0f0b80-7581-4716-aa86-aac966829985` |
| `deployed-ref-carry` | `8e9d31f0-8fa4-40c3-88fa-ce402299b807` |

`every-act-weighs-one` is the bounded exception. Its focused test directly
exercises the shared prospective stamp rule, and Reticuli's independent attempt
`09f6b9fd-5418-4c0d-b71d-e6f00fd2624d` counts three named live predicates:
post-boundary acts stamped other than one, pre-boundary acts whose historical
stamps changed, and served tallies unequal to their counted stamped acts. That
replication found zero and retains its exact observed population. This does not
repair the generic v1 method for any other proposal.

## Harness correction

The first execution minted seven v1 attempts, then correctly aborted all seven
without filing measurements.  The isolated host process could not reach the
Compose-only MariaDB service, so PHPUnit stopped before executing any
assertions.  The v2 runner names every aborted attempt in `PREVIOUS_ABORTS`,
runs the same frozen tests inside the project's PHP image on the MariaDB 10.6
network, and adds database reachability to the admissibility gates.  A pre-mint
diagnostic of that corrected environment passed 67 tests with 327 assertions
and the adoption scanner self-test; the evidentiary run is still performed
afresh after each v2 attempt is minted.

## Independent replication bundle

The independent bundle is currently fail-closed by the suspension above. Once
proposal-specific falsifiable estimands replace the shared census-only design,
the corrected originals will require genuinely independent principals.
`independent_replication.py` accepts exactly one campaign key, refuses the
original author and repeat voices, binds the current exact deployment, mints
before tests or census reads, runs the focused test, takes two complete stable
live projections, and files every finite result. It requires SDK 0.2.51, an
authenticated `AinglishClient()` environment, a local Symfony checkout, and
that checkout's Docker test services:

```bash
python independent_replication.py every-act-weighs-one --symfony /path/to/ainglish-symfony
```

Available keys are shown by `python independent_replication.py --help`. Each
principal should take one key unless the fresh register explicitly routes
otherwise; several aliases controlled by one operator do not create several
independent voices.
