"""Publish all numeric sensitivity cases, with Monte Carlo uncertainty and scope."""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def wilson(k, n, z=1.959963984540054):
    if not (0 <= k <= n and n > 0):
        raise ValueError('invalid count')
    p = k/n
    centre = (p + z*z/(2*n))/(1 + z*z/n)
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/(1 + z*z/n)
    return (0.0 if k == 0 else max(0, centre-half),
            1.0 if k == n else min(1, centre+half))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('work', type=Path)
    args = parser.parse_args()
    output = HERE / 'results'
    output.mkdir(exist_ok=True)
    rows = []
    for n in (300, 600, 1200):
        name = f'oc-n{n}.csv'
        raw = (args.work / name).read_bytes()
        (output / name).write_bytes(raw)
        batch = list(csv.DictReader(raw.decode().splitlines()))
        assert len(batch) == 12 and all(int(r['trials']) == 1000 for r in batch)
        rows.extend(batch)
    for source, name in ((args.work / 'oc-design.json', 'design.json'),
                         (args.work / 'matrices' / 'matrix-receipts.json', 'matrix-receipts.json')):
        (output / name).write_bytes(source.read_bytes())
    assert len(rows) == 36
    report = [
        '# Numeric design sensitivity: all prespecified cases', '',
        '**Not observed Ainglish evidence. No target or qualification inference occurred.**', '',
        'Two forms, two synthetic readers, 1,000 independent simulated original/replica pairs',
        'in every case. N is distinct synthetic worlds **per form**, so one run has 4N',
        'target cells. Intervals use the SDK 0.2.61 hash allocation and 2,000 SHA-counter',
        'bootstrap draws, with the proposed common-mask per-form reading. These are',
        'marginal item-bootstrap intervals, not simultaneous confidence coverage.', '',
        '“Both pass + overlap” requires pooled and both form lower bounds >= -5 pp,',
        'no exactly-zero/exactly-one form arm in either study, and pooled/form interval',
        'intersection across studies. This is **CAD preservation plus numeric overlap**,',
        'not the complete commensurability/independence/settlement pipeline or ratification.',
        'It excludes token benefit, qualifications, author accuracy/safety endpoints and ballots.', '',
        'Parenthesized bounds are 95% Wilson **Monte Carlo** intervals for a simulated',
        'frequency, not confidence intervals about the language. They are pointwise,',
        'not simultaneous over this table. Method: [NIST](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).', '',
        '| Scenario | N | Cells/run | Original pass | Both pass + overlap (MC interval) | Original held: degenerate | Form-0 / form-1 / pooled coverage |',
        '|---|---:|---:|---:|---:|---:|---|',
    ]
    for r in rows:
        n, trials = int(r['n_worlds_per_form']), int(r['trials'])
        k = int(r['support_both_and_overlap']); lo, hi = wilson(k, trials)
        cov = ' / '.join(f'{100*int(r[c])/trials:.1f}%' for c in ('cover_form0','cover_form1','cover_pooled'))
        report.append(f"| {r['scenario']} | {n} | {4*n} | {100*int(r['support_original'])/trials:.1f}% | "
                      f'{100*k/trials:.1f}% ({100*lo:.1f}–{100*hi:.1f}%) | '
                      f"{100*int(r['degenerate_original'])/trials:.1f}% | {cov} |")
    report += ['', '## Consequences for choosing a study', '',
        '- At 95% accuracy in both arms, the numeric joint pass/overlap frequency rises',
        '  from 40.1% at 1,200 target cells/run to 89.6% at 2,400 and 98.9% at 4,800.',
        '  These are conditional synthetic operating characteristics, not a selected N.',
        '- At marked 94% versus careful-English 96%, even the 4,800-cell envelope gives',
        '  only 70.2% joint pass/overlap. In 626/1,000 study pairs that also pass/overlap,',
        '  the original pooled interval excludes zero below. That is 626/702 of those',
        '  numeric successes: a tolerated-loss test does not remove the separate current',
        '  confirmed-loss veto. This study does not create a formal confirmation.',
        '- At 99.9% equality, 78.9% of originals are held at 4,800 cells and only 5.5%',
        '  of pairs pass. Refusing zero-variance certainty is defensible, but this method',
        '  may be inefficient near ceiling. Do not degrade the comparator, seek a worse',
        '  reader or rerun until errors occur to evade the guard.',
        '- When four nominal worlds share an unmodelled frame, the violating case has',
        '  only about 85–87% coverage. Nominal 95% labels do not repair pseudoreplication.',
        '  Sample independent world units or predeclare an appropriate clustered method;',
        '  paraphrases/option swaps are not extra independent worlds.',
        '- Opposite reader effects can average away. This simulation uses the actual',
        '  per-arm reader-cell allocation, not an assumed equal-reader estimand. It does',
        '  not establish per-reader safety or generalize to unmeasured models.',
        '- “One percent absent at random” is a sensitivity calculation, not a blanket',
        '  permission to discard outputs. Empty/unparsed/fault outcomes must obey the',
        '  official harness and its preregistered denominators and yield guards.', '',
        'No final sample size, bank, author amendment, accepted replication seat or run',
        'has been authorized by this report. Near-ceiling, dependent and safety cases',
        'must be considered by the independent design reviewer, not filtered away.', '',
        '## Reproduction and numerical correction', '',
        'See README.md for the commands. Source hashes and the complete fixed scenario',
        'list/streams are pinned by results/design.json. Matrix hashes and arm counts',
        'are published; the 33.6 MB of regenerable binary matrices are not committed.',
        'Seven native/SDK parity and boundary tests passed. Four separate rule-scope',
        'witness tests are illustrative specification checks, not production tests.', '',
        'An internal initial run accumulated expected cell probabilities in floating',
        'point, producing spurious coverage failures for zero-width intervals around',
        'a true zero effect. Before publication this was fixed using exact homogeneous',
        'probabilities or analytic allocation-weighted reader means, with explicit',
        'zero-truth and perfect-guard tests. The entire unchanged 36-case grid was rerun.',
        'Decisions/overlap/coverage now use four-decimal half-away-from-zero published',
        'bounds; raw quantiles are used for SDK parity checks. This is a simulation',
        'correction, not an alteration of any measured language outcome.', '',
        'The two simulated executions are statistically independent streams, not',
        'independent human/agent participation. Actual independence requires real',
        'separate participants and independently authored, disjoint inputs.', '',
    ]
    (HERE / 'NUMERIC-RESULTS.md').write_text('\n'.join(report))

    source = HERE.parent / 'decision-route-audit-2026-09-16/preservation_power.py'
    spec = importlib.util.spec_from_file_location('binomial_witness', source)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    # Known published exact interval, independently expressed boundary identities.
    assert abs(mod.lower(4, 20, .05)-.071354) < 1e-6
    assert abs(mod.upper(4, 20, .05)-.401029) < 1e-6
    auxiliary = []
    for n in (64, 128, 256, 512):
        auxiliary.append({'independent_units_per_endpoint': n,
            'one_sided_tail': .05,
            'floor_90_when_truth_95': mod.lower_pass_power(n, .95, .90, .05),
            'cap_5_when_truth_1': mod.upper_pass_power(n, .01, .05, .05)})
    (output / 'auxiliary-feasibility.json').write_text(json.dumps({
        'scope': 'Standalone independent Bernoulli endpoint illustration; not a complete approved instrument, simultaneous method, target-bank allocation or journal filing plan.',
        'input_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'rows': auxiliary}, indent=2)+'\n')
    print(json.dumps({'cases': len(rows), 'simulation_pairs': 36000,
                      'reader_calls': 0, 'output': str(output), 'auxiliary': auxiliary}))


if __name__ == '__main__':
    main()
