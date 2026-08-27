#!/usr/bin/env python3
"""Audit manifest-bound carrier coverage and the role-cardinality semantic seams offline."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(name: str) -> dict:
    value = json.loads((ROOT / name).read_text(encoding="utf-8"))
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected, name
    return value


def audit_template(name: str, expected_strata: int) -> tuple[dict, list[dict]]:
    value = checked(name)
    contract = value["settlement_strata"]
    assert 1 <= len(contract) <= 64 and len(contract) == expected_strata
    assert len({row["id"] for row in contract}) == len(contract)
    assert all(set(row) == {"id", "weight"} and row["weight"] > 0 for row in contract)
    rows = [row for row in value["items"] if not row.get("calibration")]
    artifact = json.loads((ROOT / value["items_artifact"]["file"]).read_text(encoding="utf-8"))
    assert artifact["items"] == value["items"]
    assert artifact["sha256"] == value["items_artifact"]["items_sha256"]
    assert hashlib.sha256(canonical(artifact["items"])).hexdigest() == artifact["sha256"]
    ids = {row["id"] for row in contract}
    assert all(row.get("settlement_stratum") in ids for row in rows)
    assert set(row["settlement_stratum"] for row in rows) == ids
    assert all("settlement_stratum" not in row for row in value["items"] if row.get("calibration"))
    assert value["activation"]["runnable"] is False
    assert value["model_calls"] == value["governance_writes"] == 0
    return value, rows


def main() -> None:
    repeat, repeat_rows = audit_template("repeat-restore.template.json", 16)
    repeat_counts = Counter(row["settlement_stratum"] for row in repeat_rows)
    assert set(repeat_counts.values()) == {16}
    assert all(len(ident.split(".")) == 3 for ident in repeat_counts)
    assert repeat["proposal_revision"].endswith("-4")

    role, role_rows = audit_template("role-cardinality.template.json", 48)
    role_counts = Counter(row["settlement_stratum"] for row in role_rows)
    assert set(role_counts.values()) == {10}
    assert len(role_rows) == 480
    seam_truth = {}
    for cell, expected in ((6, {"yes", "no"}), (9, {"cannot tell"}),
                           (10, {"cannot tell"}), (11, {"cannot tell"})):
        subset = [row for row in role_rows if row["strata"]["cell"] == cell]
        assert len(subset) == 40
        assert {row["form"] for row in subset} == {"one-or-more", "exactly-one"}
        assert {row["comparison"] for row in subset} == {"careful", "bare"}
        assert len({row["strata"]["role"] for row in subset}) == 10
        answers = {row["answer"] for row in subset}
        assert answers == expected
        seam_truth[f"cell-{cell:02d}"] = {
            "items": len(subset), "roles": 10, "served_answers": sorted(answers),
        }
    # Cell 06 alternates positive/negative question polarity, so yes/no surface answers differ
    # while the semantic fact stays constant: witness-only participants are outside the named role.
    assert all(
        ("excluded" in row["question"] and row["answer"] == "yes")
        or ("increase" in row["question"] and row["answer"] == "no")
        for row in role_rows if row["strata"]["cell"] == 6
    )

    replacement_receipts = {}
    for key, count in (("preference", 3), ("persistence", 2), ("may", 2)):
        value, rows = audit_template(f"{key}-replacement-original.template.json", count)
        assert value["replicates_hash"] is None
        assert len(value["legacy_original_hash"]) == 64
        assert value["filing_mode"].startswith("new stratified original")
        replacement_receipts[key] = dict(Counter(row["settlement_stratum"] for row in rows))

    report = {
        "kind": "dexagon.ainglish.manifest-bound-flagship-carrier-audit.v1",
        "status": "ready_when_external_gates_clear",
        "repeat_restore": {"scientific": len(repeat_rows), "strata": dict(repeat_counts)},
        "role_cardinality": {
            "scientific": len(role_rows), "strata": len(role_counts),
            "items_per_stratum": sorted(set(role_counts.values())),
            "role_scope_seams": seam_truth,
        },
        "replacement_originals": replacement_receipts,
        "legacy_rule": "No template attempts to attach strata to a legacy pooled original.",
        "model_calls": 0,
        "governance_writes": 0,
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    (ROOT / "audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
