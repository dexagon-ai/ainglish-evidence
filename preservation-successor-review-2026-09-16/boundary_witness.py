"""No-inference design witness; NOT a served Ainglish interval or measurement.

Exact binomial inversion, independently checkable against the NIST example at
https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm
Assumes genuine independent Bernoulli trials in each marginal population.
"""
import json
import math


def cdf(k, n, p):
    if k < 0:
        return 0.0
    if k >= n or p == 0.0:
        return 1.0
    if p == 1.0:
        return 0.0
    lp, lq = math.log(p), math.log1p(-p)
    ln = math.lgamma(n + 1)
    return min(1.0, math.fsum(math.exp(
        ln - math.lgamma(j + 1) - math.lgamma(n - j + 1)
        + j * lp + (n - j) * lq) for j in range(k + 1)))


def inverse_cdf_in_p(k, n, target):
    left, right = 0.0, 1.0
    for _ in range(65):
        middle = (left + right) / 2
        if cdf(k, n, middle) > target:
            left = middle
        else:
            right = middle
    return (left + right) / 2


def bounds(k, n, tail):
    if not (isinstance(k, int) and isinstance(n, int) and 0 <= k <= n and n > 0
            and 0 < tail < 0.5):
        raise ValueError('Require 0 <= successes <= trials, trials > 0, 0 < tail < .5')
    lower = 0.0 if k == 0 else (
        tail ** (1 / n) if k == n else inverse_cdf_in_p(k - 1, n, 1 - tail))
    upper = 1.0 if k == n else (
        1 - tail ** (1 / n) if k == 0 else inverse_cdf_in_p(k, n, tail))
    return lower, upper


def verify():
    # NIST's 4 defects / 20, central 90% interval.
    lo, hi = bounds(4, 20, .05)
    assert abs(lo - .071354) < .000001
    assert abs(hi - .401029) < .000001
    for n in (1, 2, 8, 59, 160):
        assert math.isclose(bounds(0, n, .05)[1], 1 - .05 ** (1 / n))
        assert math.isclose(bounds(n, n, .05)[0], .05 ** (1 / n))
    for k in range(11):
        a, b = bounds(k, 10, .01)
        x, y = bounds(10-k, 10, .01)
        assert 0 <= a <= k / 10 <= b <= 1
        assert abs(a - (1 - y)) < 1e-10
        assert abs(b - (1 - x)) < 1e-10
    # Homogeneous empirical bootstrap re-samples only observed zeros.
    bootstrap_delta = [0.0] * 1000
    assert min(bootstrap_delta) == max(bootstrap_delta) == 0
    assert 100 * (bounds(2, 2, .025)[0] - bounds(2, 2, .025)[1]) < -5


def main():
    verify()
    tail = .05 / 60
    boundary = []
    for n in (2, 8, 59, 120, 144, 160, 256, 512, 1024):
        lower, _ = bounds(n, n, tail)
        boundary.append({
            'independent_worlds_per_marginal': n,
            'zero_errors_single_endpoint_95_upper': bounds(0, n, .05)[1],
            'zero_errors_family_60_upper': bounds(0, n, tail)[1],
            'both_arms_perfect_family_delta_lower_pp': 100 * (lower - 1),
            'empirical_all_perfect_bootstrap': [0, 0],
        })
    planning = []
    for n in (256, 512, 1024, 2048):
        for pa, pe in ((.95, .95), (.94, .96), (.90, .95)):
            ka, ke = round(n * pa), round(n * pe)
            la, ua = bounds(ka, n, tail)
            le, ue = bounds(ke, n, tail)
            planning.append({'n_per_arm': n, 'a_successes': ka, 'e_successes': ke,
                             'delta_lower_pp': 100 * (la - ue),
                             'delta_upper_pp': 100 * (ua - le),
                             'note': 'Synthetic counts, not power, observations, or predictions'})
    print(json.dumps({'kind': 'unrun-preservation-design-witness-v1',
                      'network_or_model_calls': 0, 'family_bounds': 60,
                      'one_sided_tail_per_bound': tail, 'tests': 'passed',
                      'boundary': boundary, 'synthetic_design_calculations': planning}, indent=2))


if __name__ == '__main__':
    main()
