# Shadow pilot results — no gate change

The frozen plan ran 5,000 independent study pairs in each of 32 known-truth
population/sample-size conditions. Each pair was assessed under three duplicate
rendering multipliers, giving 96 reported conditions. These reused multiplier
conditions are not extra independent experiments. All six candidate rules and
all outcomes are in `bounded-prerequisite-results.json`; no Ainglish measurement
was submitted and no current allowance changed.

The useful result is a warning in both directions:

- Two sample means meeting the allowance need not mean the population meets it.
  With eight independent clusters in the rare-tail population and one true cell
  mean of 3.25 against the fixed allowance of 3, the sample-only rule falsely
  passed **44.28%** of study pairs (Monte Carlo 95% Wilson interval 42.91–45.66%).
- Counting cloned renderings as independent made the nominal simultaneous bounds
  unreliable. Worst observed coverage was **30.24%** (28.98–31.53%), in the
  two-point, one-failing-cell, 512-cluster, 64-duplicate condition.
- The cluster-normal approximation was also unreliable with few clusters and a
  rare tail: worst observed coverage **38.32%** (36.98–39.68%). Naming clusters
  alone does not supply a small-sample guarantee.
- The conservative, two-study simultaneous cluster-Hoeffding bound had worst
  observed coverage **99.92%** (99.79–99.97%) and no observed false passes in the
  failing-population conditions. But it passed **none** of the eight-cluster
  comfortable populations: with so little independent information it is often
  too conservative to move work forward.

This does not establish a good new governance rule. It establishes why “both are
under budget” is not an adequate population test, why duplicated templates cannot
buy precision, and why a mathematically valid bound may still be impractical.
The code only has the stated independent bounded clusters because it generated
them. The real language population generally needs a defensible frame first.

Recommendation: keep the proposal report-only. Ask for an independently reviewed,
prospectively fixed sampling frame and a practical minimum independent-unit budget
before proposing admission changes. If that cannot be specified, report the cost
sample descriptively and keep its uncertainty unresolved. Do not reinterpret old
member spans as confidence bounds or tune the allowance to the observed noise.

Present tokenizer cost, reader understanding, and hoped-for future trained-model
efficiency remain separate questions. A future training strategy does not alter
the fixed allowance or retrospectively turn today's cost samples into evidence
about an unmeasured tokenizer.
