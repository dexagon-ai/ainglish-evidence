"""Zero-inference planning sensitivity, NOT a live result or a final NI certificate.

Normal planning approximation: equal true accuracy p in each arm; variance of the difference
2*p*(1-p)/n; one-sided alpha .05; preservation margin .05. Fixed panels and authored frame
clusters violate naive cell independence, so these are explicitly optimistic IID references.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
from statistics import NormalDist

def ni_reference_power(n_per_arm, accuracy, margin=.05, alpha=.05):
    if n_per_arm <= 0 or not 0 < accuracy < 1:
        raise ValueError("Need positive n and interior reference accuracy")
    se = math.sqrt(2 * accuracy * (1-accuracy) / n_per_arm)
    return NormalDist().cdf(margin / se - NormalDist().inv_cdf(1-alpha))

def worlds_for_reference_power(accuracy, per_form_power=.9, readers=2):
    z = NormalDist().inv_cdf(.95) + NormalDist().inv_cdf(per_form_power)
    n_per_arm = 2 * accuracy * (1-accuracy) * (z/.05)**2
    worlds = math.ceil((n_per_arm * 4 / readers) / 12) * 12
    return worlds

def zero_error_upper(n, alpha=.05):
    if n <= 0:
        raise ValueError("Need a positive number of independent observations")
    return -math.expm1(math.log(alpha) / n)

def report():
    rows = []
    for worlds in (144, 576, 660, 1248):
        for accuracy in (.9, .95, .98):
            n = worlds / 2  # 2 readers, 2 forms, 2 arms, ideal balanced exposure
            power = ni_reference_power(n, accuracy)
            rows.append({"worlds": worlds, "readers": 2, "per_form_per_arm_cells_ideal": n,
                         "reference_equal_accuracy": accuracy, "per_form_power_iid_normal": round(power, 4),
                         "both_forms_lower_bound_if_each_has_this_power": round(max(0, 1-2*(1-power)), 4)})
    return {
        "kind": "ainglish.prospective-planning-only.v1", "observed_reader_calls": 0,
        "method": "normal approximation under equal arm accuracy; alpha .05 one-sided, margin 5pp",
        "rows": rows,
        "worlds_for_90_percent_per_form_power_iid_reference": {str(p): worlds_for_reference_power(p) for p in (.9, .95, .98)},
        "zero_errors_one_sided_95_percent_upper_error_probability": {str(n): round(zero_error_upper(n), 6) for n in (8,16,18,32,36,59,72)},
        "assumptions_and_limits": [
            "No empirical results enter these calculations; no target model is called.",
            "N is ideal balanced cells. The official hashed assignment must be audited after the exact roster is frozen.",
            "Cells sharing a world, a reader or an authored frame can be correlated; these IID figures do not establish effective power.",
            "The two-form lower bound is the union bound on failure probabilities, not an assertion that forms are independent.",
            "Zero-error exact-binomial bounds require independent exchangeable trials; they illustrate why a perfect small sample is not certainty.",
            "Do not run 144 then expand conditionally on its observed result. Any larger original must be selected before target exposure.",
            "The server CAD interval, point-based bounded prerequisites and a separate statistical NI analysis are distinct objects.",
        ],
        "sources": [
            "https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm",
            "https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm",
        ],
    }

if __name__ == "__main__":
    result = report()
    (Path(__file__).resolve().parent / "PLANNING-POWER.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
