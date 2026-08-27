#!/usr/bin/env python3
"""Offline structural and semantic audit for the five modern flagship carriers."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
KEYS = ("clusivity", "addressee", "uncertainty", "delegation", "collectivity")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = value.pop("content_sha256")
    assert hashlib.sha256(canonical(value)).hexdigest() == expected, path.name
    value["content_sha256"] = expected
    return value


def main() -> None:
    report = {}
    all_ids = set()
    for key in KEYS:
        template = checked(ROOT / f"{key}.template.json")
        artifact = json.loads((ROOT / template["items_artifact"]["file"]).read_text(encoding="utf-8"))
        assert artifact["items"] == template["items"]
        assert hashlib.sha256(canonical(artifact["items"])).hexdigest() == artifact["sha256"]
        assert artifact["sha256"] == template["items_artifact"]["items_sha256"]
        assert template["items_artifact"]["published_url"].endswith("/" + template["items_artifact"]["file"])
        contract = template["settlement_strata"]
        assert len(contract) == 8 and len({row["id"] for row in contract}) == 8
        assert all(set(row) == {"id", "weight"} and row["weight"] == 1 for row in contract)
        science = [row for row in template["items"] if not row.get("calibration")]
        calibration = [row for row in template["items"] if row.get("calibration")]
        counts = Counter(row["settlement_stratum"] for row in science)
        assert set(counts) == {row["id"] for row in contract} and set(counts.values()) == {6}
        assert len(science) == 48 and len(calibration) == 12
        assert all(row["english"] != row["ainglish"] and row["answer"] in row["options"] for row in science)
        assert all(row["calibration_scope"] == "target-independent" for row in calibration)
        ids = {row["id"] for row in template["items"]}
        assert len(ids) == 60 and not (all_ids & ids)
        all_ids |= ids
        assert template["model_calls"] == template["governance_writes"] == 0
        report[key] = {"scientific": 48, "calibration": 12, "strata": dict(counts)}

    # These are the exact high-risk seams the modern packets exist to keep load-bearing.
    assert set(report["delegation"]["strata"]) == {
        "no-delegation.first-hop", "no-delegation.second-hop", "no-delegation.accountability", "no-delegation.tool-nonclaim",
        "one-hop-delegation-allowed.first-hop", "one-hop-delegation-allowed.second-hop",
        "one-hop-delegation-allowed.accountability", "one-hop-delegation-allowed.tool-nonclaim",
    }
    assert set(report["collectivity"]["strata"]) == {
        f"{form}.{seam}" for form in ("each-alone", "as-one")
        for seam in ("action-count", "amount", "timing-nonclaim", "participation")
    }
    review = json.loads((ROOT / "collectivity-instrument-review.json").read_text(encoding="utf-8"))
    assert review["supportive_registered_measurement"]["value_pp"] > 0
    assert review["retained_adverse_diagnostic"]["value_pp"] < 0
    assert review["remediation"]["items_sha256"] == json.loads(
        (ROOT / "collectivity.items.json").read_text(encoding="utf-8")
    )["sha256"]
    assert set(review["remediation"]["load_bearing_seams"]) == set(report["collectivity"]["strata"])
    out = {
        "kind": "dexagon.ainglish.flagship-modern-carrier-audit.v2",
        "status": "frozen_waiting_external_gates",
        "templates": report,
        "unique_item_ids": len(all_ids),
        "model_calls": 0,
        "governance_writes": 0,
    }
    out["content_sha256"] = hashlib.sha256(canonical(out)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
