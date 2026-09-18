# Numeric feasibility: useful at equality, not a universal solution

This is a CPU-only design experiment, **not language measurement**. The design
and code were committed as `99bdece` before execution. All twelve prespecified
scenarios ran once, at 1,024 worlds per form, 1,000 synthetic original/replica
pairs per scenario and 2,000 bootstrap draws. No reader/API calls, models or
language answer keys were involved. Execution took about 33 seconds.

Full [CSV](cad-n1024.csv), [auxiliary diagnostics](auxiliary-binomial-diagnostics.json)
and [execution/matrix receipts](execution.json) are retained. The unmodified
simulator and allocation preparation are pinned by [design.json](design.json).
Synthetic outcomes and SDK allocation are separate seeds; no seed was selected
on favourable outcomes. These are finite Monte Carlo proportions under named
scenarios, not population guarantees or predictions of an actual model.

| Synthetic scenario | Both studies pass CAD | Both pass and overlap | Important limitation |
| --- | ---: | ---: | --- |
| Equal arms, independent worlds | 997/1,000 | 990/1,000 | Not full-study acceptance |
| Equal arms, shared world effects | 996/1,000 | 985/1,000 | Sharing within the world is represented |
| True two-point loss | 550/1,000 | 550/1,000 | A tolerated loss can still be hard to establish |
| True five-point boundary | 0/1,000 | 0/1,000 | Boundary is not a high-power passing case |
| True six-point violation | 0/1,000 | 0/1,000 | Adverse scenario retained |
| Five-point boundary, shared world | 0/1,000 | 0/1,000 | No passing rescue |
| Six-point violation, shared four-world frame | 0/1,000 | 0/1,000 | Form interval coverage only 879/858 of 1,000 |
| Equality, shared four-world frame | 991/1,000 | 978/1,000 | High passing rate does not validate the unit |
| Equality near ceiling | 27/1,000 | 27/1,000 | 840/1,000 originals degenerate and held |
| Opposite reader effects | 999/1,000 | 985/1,000 | Pooled/per-form success can hide reader harm |
| One harmed form hidden by pooled average | 0/1,000 | 0/1,000 | Per-form requirement retains the harm |
| One percent absence, at random | 995/1,000 | 984/1,000 | Does not cover selective/nonrandom failures |

For auxiliary 5% error limits, a one-sided per-reader 97.5% exact bound at
N=512 admits at most 15 errors. Under the **synthetic iid** true-error rate 1%,
the individual bound passes with probability 0.999919; at 2.5%, only 0.783423.
At N=128 the same limit admits one error and passes only 0.633426 at true 1%.
Thus a small clean-looking pilot does not assure precision for a ten-endpoint
bundle. These calculations are a conservative sufficient-condition diagnostic
(both reader bounds individually pass), not exact power of the proposed
averaged-bound rule. The all-twenty-bounds lower bound is often zero; zero here
means an uninformative bound, not demonstrated impossibility.

The control 90% floor is different: N=128 allows six errors in that same
per-reader diagnostic, with pass probability 0.999670 at true 1% error and
0.540714 at true 5% error. Near-boundary performance remains a risk.

**Decision:** hold execution. The candidate is costed, not accepted. Get author
scope/resource and independent design decisions first. In particular, the
31,808-call per-study envelope is not justified merely by CAD's high synthetic
equality power. The prototype controls, sampling validity, auxiliary methods,
protocol operativity and independent replica remain separate prerequisites.
