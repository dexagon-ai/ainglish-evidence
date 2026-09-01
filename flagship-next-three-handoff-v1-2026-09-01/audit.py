#!/usr/bin/env python3
"""Fail-closed offline audit for the next-three flagship handoff."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(value: dict) -> str:
    expected = value["content_sha256"]
    material = {key: item for key, item in value.items() if key != "content_sha256"}
    assert hashlib.sha256(canonical(material)).hexdigest() == expected
    return expected


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    index_sha = checked(index)
    expected = {
        "acknowledgement-force": (160, 24, {"ack-as-agreement": 80, "ack-as-receipt": 80}),
        "role-cardinality": (128, 24, {"exactly-one": 64, "one-or-more": 64}),
        "will-force": (120, 24, {"will-as-forecast": 40, "will-as-plan": 40, "will-as-promise": 40}),
    }
    all_ids = set()
    scientific_ids = set()
    calibration_ids_by_campaign = {}
    for key, (real_count, calibration_count, forms) in expected.items():
        row = index["campaigns"][key]
        path = REPO / row["items"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["items_file_sha256"]
        items = json.loads(path.read_text(encoding="utf-8"))
        assert hashlib.sha256(canonical(items)).hexdigest() == row["items_canonical_sha256"]
        science = [item for item in items if item.get("calibration") is not True]
        calibration = [item for item in items if item.get("calibration") is True]
        assert len(science) == real_count and len(calibration) == calibration_count
        assert Counter(item["form"] for item in science) == Counter(forms)
        assert all(item["answer"] in item["options"] for item in items)
        assert all(len(item["options"]) == len(set(item["options"])) for item in items)
        ids = {item["id"] for item in items}
        assert len(ids) == len(items)
        campaign_scientific_ids = {item["id"] for item in science}
        assert not campaign_scientific_ids.intersection(scientific_ids)
        scientific_ids.update(campaign_scientific_ids)
        calibration_ids_by_campaign[key] = {item["id"] for item in calibration}
        all_ids.update(ids)

    acknowledgement = json.loads((REPO / index["campaigns"]["acknowledgement-force"]["items"]).read_text(encoding="utf-8"))
    will = json.loads((REPO / index["campaigns"]["will-force"]["items"]).read_text(encoding="utf-8"))
    source_will = json.loads((REPO / "modal-operational-comprehension-carriers-2026-08-25/panel/will.json").read_text(encoding="utf-8"))["items"]
    assert [row for row in will if row.get("calibration") is True] == [
        row for row in acknowledgement if row.get("calibration") is True
    ]
    assert [row for row in will if row.get("calibration") is not True] == [
        row for row in source_will if row.get("calibration") is not True
    ]
    assert calibration_ids_by_campaign["will-force"] == calibration_ids_by_campaign["acknowledgement-force"]
    assert not calibration_ids_by_campaign["role-cardinality"].intersection(
        calibration_ids_by_campaign["acknowledgement-force"]
    )

    receipt = json.loads((ROOT / "live-receipt.json").read_text(encoding="utf-8"))
    receipt_sha = checked(receipt)
    assert set(receipt["proposals"]) == {row["slug"] for row in index["campaigns"].values()}
    for proposal in receipt["proposals"].values():
        assert proposal["stage"] == "measured"
        assert proposal["evidence_ready"] is False
        assert proposal["missing_evidence"] == ["comprehension_accuracy_delta"]
        assert proposal["unresolved_evidence"] == []
        assert proposal["opposing_evidence"] == []
        assert proposal["current_action"]["metric"] == "comprehension_accuracy_delta"

    result = {
        "kind": "dexagon.ainglish.flagship-next-three-handoff-audit.v1",
        "status": "passed_waiting_external_reader_gate",
        "index_sha256": index_sha,
        "live_receipt_sha256": receipt_sha,
        "campaigns": len(expected),
        "scientific_items": 408,
        "calibration_items": 72,
        "unique_scientific_item_ids": len(scientific_ids),
        "unique_item_ids": len(all_ids),
        "deliberately_reused_calibration_ids": len(
            calibration_ids_by_campaign["will-force"].intersection(
                calibration_ids_by_campaign["acknowledgement-force"]
            )
        ),
        "model_downloads": 0,
        "model_calls": 0,
        "governance_writes": 0,
        "content_sha256": "",
    }
    result["content_sha256"] = hashlib.sha256(canonical({
        key: value for key, value in result.items() if key != "content_sha256"
    })).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
