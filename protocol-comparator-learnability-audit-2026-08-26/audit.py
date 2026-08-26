#!/usr/bin/env python3
"""Recompute live denominators and the two protocol decision tables."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
COMPARATOR_SLUG = "comparator-class-claim-carriers-a-row-may-declare-its-compre"
NAMED = {
    "proxy-m-say-when-the-evidence-you-measured-is-a-proxy-for-th-2",
    "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2",
    "this-once-from-now-on-does-this-instruction-apply-to-this-ta",
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2",
    "approx-n-approximation-marker-parenthesized-d-1-robust-5",
}
LEARNABILITY = (
    {"row": "approx(N)", "delta": -0.016, "lo": -0.057, "hi": 0.026},
    {"row": "proxy(M)", "delta": 0.132, "lo": 0.049, "hi": 0.229},
    {"row": "rather-not", "delta": 0.141, "lo": -0.005, "hi": 0.286},
    {"row": "this-once", "delta": 0.078, "lo": 0.010, "hi": 0.146},
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    return value


def comparator_class(kind: str | None) -> str:
    if kind and "careful" in kind:
        return "careful"
    if kind and kind.startswith("bare-"):
        return "bare"
    return "other"


def point_stance(delta: float) -> str:
    return "supports" if delta > 0.02 else ("opposes" if delta < -0.02 else "neutral")


def interval_stance(lo: float, hi: float) -> str:
    return "supports" if lo > 0.02 else ("opposes" if hi < -0.02 else "neutral")


def main() -> None:
    snapshot = checked(ROOT / "snapshot.json")
    population = snapshot["population"]
    object_carriers = []
    for row in population:
        carrier = row.get("claim_carrier") or []
        if any(isinstance(value, dict) for value in carrier):
            object_carriers.append(row["slug"])
    classes = {slug: set() for slug in NAMED}
    for row in snapshot["named_comprehension_rows"]:
        classes[row["slug"]].add(comparator_class(row.get("comparator_kind")))
    both = sorted(slug for slug, values in classes.items() if {"bare", "careful"} <= values)
    careful_only = sorted(slug for slug, values in classes.items() if "careful" in values and "bare" not in values)
    denominators = [len(object_carriers), len(both), len(careful_only), len(population) - len(NAMED)]
    declared = snapshot["protocols"][COMPARATOR_SLUG]["protocol_meta"]["blast_radius"]["row_classes"]
    declared_eligible = [row["eligible"] for row in declared]
    synthetic = [
        {"cell": "win-bare/pass-careful", "bare_delta": 25, "careful_delta": 0, "carrier_only_ready": True, "carrier_plus_safety_ready": True},
        {"cell": "win-bare/fail-careful", "bare_delta": 25, "careful_delta": -30, "carrier_only_ready": True, "carrier_plus_safety_ready": False},
        {"cell": "fail-bare/pass-careful", "bare_delta": 0, "careful_delta": 0, "carrier_only_ready": False, "carrier_plus_safety_ready": False},
        {"cell": "missing-bare/pass-careful", "bare_delta": None, "careful_delta": 0, "carrier_only_ready": False, "carrier_plus_safety_ready": False},
    ]
    learnability = [{**row, "point_deadband_stance": point_stance(row["delta"]), "paired_interval_deadband_stance": interval_stance(row["lo"], row["hi"])} for row in LEARNABILITY]
    report = {
        "kind": "dexagon.ainglish.protocol-comparator-learnability-audit.v1",
        "snapshot_sha256": snapshot["content_sha256"],
        "comparator": {
            "live_rows": len(population),
            "object_comparator_carriers": object_carriers,
            "both_comparator_named_rows": both,
            "careful_only_named_rows": careful_only,
            "recomputed_row_class_denominators": denominators,
            "declared_eligible_column": declared_eligible,
            "eligible_column_matches_denominators": declared_eligible == denominators,
            "synthetic_readiness": synthetic,
            "formal_measurement_filed": False,
            "reason_not_filed": "zero-at-deploy cannot exercise the future comparator branch, and the stated eligible column is not the live denominator table",
        },
        "learnability": {
            "source": "Ainglish PR 97 commit 4fe99a6 paired per-item bootstrap receipts",
            "deadband": 0.02,
            "rows": learnability,
            "point_rule_moves_from_current_fixed_0_5": sum(row["point_deadband_stance"] != "supports" for row in learnability),
            "paired_interval_rule_moves_from_current_fixed_0_5": sum(row["paired_interval_deadband_stance"] != "supports" for row in learnability),
        },
        "model_calls": 0,
        "governance_writes": 0,
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    (ROOT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "live_rows": len(population),
        "object_carriers": len(object_carriers),
        "recomputed_denominators": denominators,
        "declared_eligible": declared_eligible,
        "unsafe_synthetic_cells": sum(row["carrier_only_ready"] and not row["carrier_plus_safety_ready"] for row in synthetic),
        "point_rule_moves": report["learnability"]["point_rule_moves_from_current_fixed_0_5"],
        "interval_rule_moves": report["learnability"]["paired_interval_rule_moves_from_current_fixed_0_5"],
        "content_sha256": report["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()

