"""Conditional binomial design calculations, not observed language evidence.

Pure Python; no model, tokenizer, network or SDK calls. Bounds use exact binomial
tail inversion. The population/sampling assumptions are stated in STUDY-DESIGN.md.
"""
import argparse
from functools import lru_cache
import json
import math
from pathlib import Path


def binom_cdf(k, n, p):
    if n < 0 or not 0 <= p <= 1:
        raise ValueError('Invalid binomial population')
    if k < 0: return 0.0
    if k >= n or p == 0: return 1.0
    if p == 1: return 0.0
    if k >= n * p:
        return max(0.0, 1.0 - binom_cdf(n-k-1, n, 1-p))
    term = math.exp(math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)
                    + k*math.log(p)+(n-k)*math.log1p(-p))
    total = term
    for j in range(k, 0, -1):
        term *= j / (n-j+1) * (1-p) / p
        total += term
    return min(1.0, total)


@lru_cache(maxsize=None)
def cp_upper(k, n, alpha=.025):
    if n <= 0 or not 0 <= k <= n or not 0 < alpha < 1:
        raise ValueError('Invalid exact-bound arguments')
    if k == n: return 1.0
    low, high = 0.0, 1.0
    for _ in range(60):
        middle = (low + high) / 2
        if binom_cdf(k, n, middle) > alpha: low = middle
        else: high = middle
    return (low + high) / 2


def cp_lower(k, n, alpha=.025):
    return 1 - cp_upper(n-k, n, alpha)


def preservation_pass(ka, na, ke, ne):
    lower_a = cp_lower(ka, na)
    upper_e = cp_upper(ke, ne)
    return lower_a - upper_e > -.05 and lower_a >= .90


def probable_counts(n, p):
    if p == 1: return [(n, 1.0)]
    if p == 0: return [(0, 1.0)]
    # Excluded tiny masses are reported, not silently renormalized.
    result = []
    for k in range(n + 1):
        mass = math.exp(math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)
                        + k*math.log(p)+(n-k)*math.log1p(-p))
        if mass >= 1e-14: result.append((k, mass))
    return result


def conditional_power(n, pa, pe):
    a, e = probable_counts(n, pa), probable_counts(n, pe)
    al = {k: cp_lower(k, n) for k, _ in a}
    eu = {k: cp_upper(k, n) for k, _ in e}
    probability = min(1.0, max(0.0, math.fsum(
        ma*me for ka, ma in a for ke, me in e
        if al[ka] - eu[ke] > -.05 and al[ka] >= .90)))
    omitted = max(0.0, 1 - math.fsum(v for _, v in a)*math.fsum(v for _, v in e))
    return {
        'n_per_arm_reader_form': n, 'assumed_ainglish_accuracy': pa,
        'assumed_english_accuracy': pe, 'single_reader_form_power_lower': probability,
        'discarded_probability_mass_upper': omitted,
        'four_reader_form_tests_joint_power_union_lower': max(0.0, 1-4*(1-probability)),
        'both_runs_eight_tests_joint_power_union_lower': max(0.0, 1-8*(1-probability)),
        'excludes': 'Domain/boundary safety screens, transport loss, instrument defects, '
                    'replication point matching and current server ceiling rule.',
    }


def report():
    return {
        'kind': 'CONDITIONAL_DESIGN_CALCULATIONS_NOT_OBSERVED_RESULTS',
        'numerics': 'Floating-point evaluation of exact-tail formulas; endpoint probabilities '
                    'are clamped to [0,1]. Reported union bounds are numerical approximations.',
        'tail_per_proportion': .025,
        'decision': 'Each reader/form requires L_A-U_E > -0.05 and L_A >= 0.90. '
                    'All four tests must pass; conjunction is an intersection-union decision, '
                    'not simultaneous four-test interval coverage.',
        'scope': 'IID draws within each fixed reader/form from one declared task generator; '
                 'not evidence about human readers, unseen frame populations, future models, '
                 'or independence of the two models. No observations exist.',
        'planning': [conditional_power(n, pa, pe)
                     for n in (384, 768, 900, 1024, 1400)
                     for pa, pe in ((.99,.99), (.97,.97), (.95,.95), (.93,.93),
                                    (.95,.97), (.92,.97))],
        'ceiling_examples': [{'n_per_arm': n,
            'all_correct_lower_delta_pp': 100*(cp_lower(n,n)-1),
            'all_correct_absolute_accuracy_lower': cp_lower(n,n),
            'conditional_decision': preservation_pass(n,n,n,n)}
            for n in (36, 72, 900, 1024, 1400)],
        'current_server': 'Both arms >= .90 remain ceiling/unresolved, even when the '
                          'separate prospective conditional preservation test passes. '
                          'No new acceptance rule is enacted here.',
    }


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    value = report()
    with args.output.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')
    print('Conditional planning complete; zero reader calls.')
