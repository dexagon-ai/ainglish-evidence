"""Frozen human-authored designs for modern successors to legacy token originals."""

SOURCE_ATTEMPT = "20309d7b-de8a-4526-9a28-288a84488dc0"
SOURCE_HASH = "921e17ac1393b536cad4121697864280922f8d05131abf15e21890d92cf2d485"
SLUG = "mean-of-population-ref-value-median-of-population-ref-value"


POPULATIONS = [
    ("packet-loss-ppm@edge-west-2026w35-v3", "18 ppm", "7 ppm"),
    ("response-ms@checkout-canary-2026-09-01-v4", "184 ms", "61 ms"),
    ("queue-wait-s@warehouse-night-2026-08-v2", "93 s", "44 s"),
    ("invoice-gbp@studio-2026q2-audit-v5", "GBP 812", "GBP 470"),
    ("temperature-c@greenhouse-bay7-2026d244-v2", "21.8 C", "21.2 C"),
    ("repair-hours@fleet-north-2026h1-v3", "6.4 h", "3.1 h"),
    ("transfer-mbps@relay-blue-2026-09-02-v6", "72 Mbps", "81 Mbps"),
    ("energy-kwh@lab-annex-2026w34-v2", "146 kWh", "119 kWh"),
    ("claim-days@mutual-2025-closed-v7", "38 days", "22 days"),
    ("rainfall-mm@catchment-elm-2026-aug-v3", "4.7 mm", "1.3 mm"),
    ("render-s@scene-cobalt-build-918-v2", "27.6 s", "19.4 s"),
    ("delivery-km@district-olive-2026w33-v4", "16.2 km", "11.0 km"),
    ("memory-mib@worker-pool-zeta-2026-09-01-v3", "742 MiB", "688 MiB"),
    ("inspection-defects@line-four-2026m08-v5", "3.6 defects", "2 defects"),
    ("call-minutes@support-tier-b-2026w32-v2", "14.1 min", "8.5 min"),
    ("yield-percent@orchard-block-c-2026-v4", "71.5 percent", "74.0 percent"),
]


def mean_items():
    rows = []
    for index, (population, mean_value, median_value) in enumerate(POPULATIONS, 1):
        rows.append({
            "id": f"mean-{index:02d}",
            "stratum": "mean-of",
            "english": (
                "The unweighted arithmetic mean of every numeric observation in the exact "
                f"finite population {population} is {mean_value}."
            ),
            "ainglish": f"mean-of({population}) = {mean_value}.",
        })
        rows.append({
            "id": f"median-{index:02d}",
            "stratum": "median-of",
            "english": (
                "The median of every numeric observation in the exact finite population "
                f"{population} is {median_value}."
            ),
            "ainglish": f"median-of({population}) = {median_value}.",
        })
    return rows


MEAN_SUCCESSOR = {
    "slug": SLUG,
    "source_attempt_id": SOURCE_ATTEMPT,
    "source_hash": SOURCE_HASH,
    "models": ["cl100k_base", "o200k_base", "p50k_base"],
    "test_set": mean_items(),
    "settlement_strata": [
        {"id": "mean-of", "weight": 1},
        {"id": "median-of", "weight": 1},
    ],
}

