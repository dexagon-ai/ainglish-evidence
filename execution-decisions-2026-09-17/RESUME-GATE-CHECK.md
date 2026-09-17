# Can the 160-call resume study advance its prerequisite?

**It can under some outcomes, but high comprehension alone will not do it.**
This is a no-inference design check, not a measurement, a prediction of reader
performance, a power analysis or a change to the accepted study.

The live proposal requires `comprehension_accuracy_delta >= 0`; learning remains
the claim carrier. The current implementation first applies its resolution
rule. Both arms at or above 0.90 in **either** required policy stratum make the
whole result unresolved. Confirmation does not remove that status. This is
consistent with the published [protocol's resolution warning](https://ainglish.org/api/v1/protocols).

The accompanying script calls the actual PHP rule components. Its synthetic
cases include:

| Example for the two policy strata | Bounded prerequisite stance |
|---|---|
| English 100%, marked 100%, both strata | Unresolved |
| English 95%, marked 97%, both strata | Unresolved |
| One stratum 95%/95%, the other 80%/85% | Unresolved |
| English 85%, marked 85%, broad interval crossing zero | Supports at the **point-threshold component only** |
| English 80%, marked 95%, both strata | Supports at that component |
| English 85%, marked 80%, both strata | Opposes |
| Both arms at the two-option chance level | Unresolved |

The fourth case is important: current `at_least: 0` is a **point** threshold
after the resolution check, not a requirement that the interval's lower bound
be nonnegative. Such a result is not scientific proof of equivalence. These
component verdicts also do not supply replication, independent eligibility,
the rest of the evidence contract, or a ratifying ballot.

## Actual frozen grid and remaining replication fragility

The fixed allocation gives resume-core 37 English / 27 marked cells and
redo-core 33 English / 31 marked cells. If the marked arm is at least 90% in
both strata, avoiding the ceiling requires English at most 33/37 and 29/33
correct respectively. That is a consequence of the rule, **not a target to
engineer by weakening English or choosing a favourable seed**.

One changed answer moves a stratum by 2.70–3.70 percentage points. In a concrete
synthetic example on this grid, the resume delta is +8.81 pp. One additional
correct English answer changes it by 2.71 pp, exceeding its current 0.881 pp
replication tolerance. The real comparison method marks that stratum as not
reproduced. Current `ReplicationSettlement::settle` still requires the stratum
point comparisons even when attested **aggregate** intervals overlap.

This is a fragility witness, not an estimate of disagreement probability.
The independent replica's fresh item IDs can give different arm counts; its
bank, final allocation and execution commitment do not yet exist. Do not tune
them to reproduce a source result. The proposed attested-stratum interval rule
is a separate, non-operative protocol proposal; this audit does not opt in.

## Decision requested before spend

Accept the exact current 160-call plan as a bounded diagnostic with these
limitations, specify a prospective revision, or decline it. Do not approve it
merely because the server preflight accepts its manifest. If both forms are
well understood, retain that result honestly even when it cannot advance the
current prerequisite. Do not weaken the careful-English comparator, drop a
policy stratum, select a seed after outcomes, or call a ceiling result a pass.

The existing author/design/replication holds remain in force. Author acceptance
of semantic golds and of separate boundary reporting is already complete and
is **not** being requested again. A favourable core result would still leave
the later learning/boundary claims and independent ballot judgment outstanding.

## Replay

`resume_gate_audit.php` runs offline against a Symfony checkout and its existing
Composer dependencies. It initializes only the pure stance dependency through
reflection; it does not call repositories, a database, readers or an API.

```sh
php resume_gate_audit.php /path/to/ainglish-symfony
```

An optional second argument supplies an existing vendor autoloader from another
checkout. `resume-gate-audit.json` records 14 passing component checks and source
file hashes. Tested source is Symfony commit
`cea11d51740329ed283b53eba01d00223f09700f`; all six audited service files are
unchanged from base commit `766bc18b4f4a7e807fbfb2da669c3e09d187df34`.
The frozen language items, manifest, seeds and call envelope are unchanged.
