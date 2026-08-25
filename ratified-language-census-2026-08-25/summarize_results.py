#!/usr/bin/env python3
"""Apply the outcome-blind editorial policy to completed census receipts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    policy = json.loads((ROOT / "flagship-selection-policy.json").read_text())
    gates = policy["gates"]
    rows = []
    for path in sorted(ROOT.glob("campaign-*.measurement.json")):
        data = json.loads(path.read_text())
        summary = data["summary"]
        cold = summary["cold"]
        reference = summary["reference"]
        cold_cal = data["request"].get("calibration", {}).get("passed") is True
        ref_path = ROOT / path.name.replace(".measurement.json", ".reference.result.json")
        ref_result = json.loads(ref_path.read_text())
        reference_cal = ref_result.get("calibration", {}).get("passed") is True
        forms = sorted(set(cold["per_form"]) | set(reference["per_form"]))
        form_rows = []
        for form in forms:
            c = cold["per_form"][form]
            r = reference["per_form"][form]
            cold_pass = (
                c["arms"]["english"] >= gates["minimum_careful_english_accuracy"] and
                c["arms"]["ainglish"] >= gates["minimum_cold_ainglish_accuracy"] and
                c["delta_pp"] >= gates["minimum_cold_delta_pp"]
            )
            reference_pass = (
                r["arms"]["english"] >= gates["minimum_careful_english_accuracy"] and
                r["arms"]["ainglish"] >= gates["minimum_reference_ainglish_accuracy"] and
                r["delta_pp"] >= gates["minimum_reference_delta_pp"]
            )
            form_rows.append({"form": form, "cold": c, "reference": r, "cold_pass": cold_pass, "reference_pass": reference_pass})
        if cold_cal and reference_cal and all(row["cold_pass"] and row["reference_pass"] for row in form_rows):
            classification = "flagship-candidate"
        elif cold_cal and reference_cal and all(row["reference_pass"] for row in form_rows):
            classification = "reference-dependent"
        else:
            classification = "not-ready"
        rows.append({
            "campaign": summary["campaign"], "classification": classification,
            "calibration": {"cold": cold_cal, "reference": reference_cal}, "forms": form_rows,
        })
    expected = len(json.loads((ROOT / "index.json").read_text())["proposal_packets"]) // 2
    report = {
        "kind": "ainglish.ratified-census-flagship-selection-report.v1",
        "policy_sha256": hashlib.sha256(canonical(policy)).hexdigest(),
        "campaigns_expected": expected, "campaigns_observed": len(rows),
        "complete": len(rows) == expected, "rows": rows,
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    (ROOT / "flagship-selection-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "complete": report["complete"],
        "counts": {label: sum(row["classification"] == label for row in rows) for label in policy["classes"]},
        "sha256": report["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
