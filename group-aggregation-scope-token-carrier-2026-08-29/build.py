#!/usr/bin/env python3
"""Freeze a balanced price carrier without loading any tokenizer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "each-group-group-set-ref-clause-groups-combined-group-set"

CASES = [
    ("regions@2026Q3", "checkout success increased"),
    ("model-families@eval-v4", "error rate stayed below 2%"),
    ("age-bands@trial-v2", "treatment recovery exceeded control"),
    ("data-centres@week-35", "p95 latency decreased"),
    ("review-teams@release-14", "defect escape rate fell"),
    ("customer-tiers@august-v3", "renewal rate exceeded 80%"),
    ("device-classes@firmware-9", "battery failures declined"),
    ("delivery-zones@summer-v2", "late arrivals stayed under 4%"),
    ("language-cohorts@benchmark-7", "exact-match accuracy improved"),
    ("risk-bands@portfolio-q3", "default rate decreased"),
    ("hospital-sites@audit-6", "readmission rate fell"),
    ("queue-classes@loadtest-11", "timeout frequency stayed below 1%"),
    ("supplier-groups@contract-v5", "on-time fulfilment improved"),
    ("school-types@term-1", "attendance exceeded last year's level"),
    ("account-plans@migration-3", "support contacts declined"),
    ("sensor-families@calibration-8", "absolute error stayed within tolerance"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    rows = []
    for index, (reference, clause) in enumerate(CASES, 1):
        rows.append(
            {
                "item_id": f"each-group-{index:02d}",
                "form": "each-group",
                "group_set_ref": reference,
                "ainglish": f"each-group({reference}): {clause}.",
                "english": f"In every group in {reference}, considered separately, {clause}.",
            }
        )
    for index, (reference, clause) in enumerate(CASES, 1):
        rows.append(
            {
                "item_id": f"groups-combined-{index:02d}",
                "form": "groups-combined",
                "group_set_ref": reference,
                "ainglish": f"groups-combined({reference}): {clause}.",
                "english": f"After observations from all groups in {reference} are combined, {clause}.",
            }
        )
    forms = ("each-group", "groups-combined")
    counts = {form: sum(row["form"] == form for row in rows) for form in forms}
    if len(rows) != 32 or counts != {form: 16 for form in forms}:
        raise SystemExit("REFUSING: pair count or form balance drift")
    if len({(row["ainglish"], row["english"]) for row in rows}) != len(rows):
        raise SystemExit("REFUSING: complete pairs are not unique")
    if any(row["ainglish"] == row["english"] for row in rows):
        raise SystemExit("REFUSING: identical arms")
    packet = {
        "kind": "ainglish.group-aggregation-scope-token-items.v1",
        "proposal_slug": SLUG,
        "metric": "token_delta",
        "forms": list(forms),
        "form_counts": counts,
        "comparison": (
            "registered assertion-scope marker versus concise complete careful English that "
            "names the same group reference and the same per-group or combined evaluation level"
        ),
        "acceptance": {"least_favourable_balanced_mean_at_most": 3},
        "evidentiary_limit": (
            "present price prerequisite only; current tokenizers were trained on English and "
            "generally not Ainglish, and token count cannot establish scope recovery"
        ),
        "test_set": rows,
    }
    packet["items_sha256"] = hashlib.sha256(canonical(rows)).hexdigest()
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target = ROOT / "token-items.json"
    if target.exists():
        raise SystemExit("REFUSING: token-items.json already exists")
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "pairs": len(rows),
                "form_counts": counts,
                "items_sha256": packet["items_sha256"],
                "content_sha256": packet["content_sha256"],
                "tokenizer_calls": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
