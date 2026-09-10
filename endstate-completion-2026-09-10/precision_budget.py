"""Illustrative, offline zero-error precision planning; never a measurement."""
import json
import math


def zero_error_upper(n, confidence=0.95, simultaneous_claims=1):
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError('n must be a positive integer independent-trial count')
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not math.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError('confidence must be strictly between zero and one')
    if isinstance(simultaneous_claims, bool) or not isinstance(simultaneous_claims, int) or simultaneous_claims < 1:
        raise ValueError('simultaneous_claims must be a positive integer')
    alpha = (1 - confidence) / simultaneous_claims
    return -math.expm1(math.log(alpha) / n)


def minimum_zero_error_n(max_error, confidence=0.95, simultaneous_claims=1):
    if not isinstance(max_error, (int, float)) or isinstance(max_error, bool) or not math.isfinite(max_error) or not 0 < max_error < 1:
        raise ValueError('max_error must be strictly between zero and one')
    zero_error_upper(1, confidence, simultaneous_claims)
    candidate = math.ceil(math.log((1-confidence)/simultaneous_claims) / math.log1p(-max_error))
    # Round-off at an exact boundary must not silently promise an unattained limit.
    while zero_error_upper(candidate, confidence, simultaneous_claims) > max_error:
        candidate += 1
    return candidate


def report():
    return {
        'kind':'ainglish.offline-precision-illustration.v1',
        'scientific_measurement':False,
        'new_governance_rule':False,
        'assumptions':'Independent Bernoulli trials; zero errors; chosen one-sided confidence. Not granted by a template corpus or reader roster.',
        'confidence':0.95,
        'upper_error_percent':{
            str(n):round(100*zero_error_upper(n),6)
            for n in [6,8,10,16,20,32,48,58,59,64,80,96,128,160]
        },
        'minimum_n_for_5_percent_one_claim':minimum_zero_error_n(0.05),
        'minimum_n_per_claim_for_5_percent_eight_simultaneous_claims_bonferroni':minimum_zero_error_n(0.05,simultaneous_claims=8),
        'warning':'Not a comprehension-delta interval, power guarantee, mandatory sample size or allowance to change a frozen study.',
    }


if __name__=='__main__':
    print(json.dumps(report(),indent=2))
