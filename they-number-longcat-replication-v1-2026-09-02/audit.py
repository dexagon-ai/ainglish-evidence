#!/usr/bin/env python3
"""Fail-closed audit of the fresh they-number replication carrier."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from ainglish import panel as panel_harness


ROOT = Path(__file__).resolve().parent
ORIGINAL_ITEMS_URL = "https://raw.githubusercontent.com/reticuli-labs/panel-artifacts/6c32a4a75c30c1e1feb41baba79f884857104974/they-one-they-many-comprehension-2026-08-29/items-run2.json"
ORIGINAL_ITEMS_SHA256 = "8417e8bf936eb47ebf3c6d2869aa50da32bdc4ad80b6c3f9dde309157a926160"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def pairs(rows: list[dict]) -> set[tuple[str, str]]:
    return {(row["english"], row["ainglish"]) for row in rows if not row.get("calibration")}


def main() -> None:
    payload = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    items = payload["items"]
    real = [row for row in items if not row.get("calibration")]
    cal = [row for row in items if row.get("calibration")]
    assert payload["reader_calls"] == index["model_calls"] == 0
    assert payload["replicates_hash"] == index["replicates_hash"]
    assert len(real) == index["scientific_items"] == 128
    assert len(cal) == index["calibration_items"] == 24
    assert len({row["id"] for row in items}) == len(items)
    assert Counter(row["form"] for row in real) == Counter({"they-one": 64, "they-many": 64})
    assert Counter(row["semantic_seam"] for row in real) == Counter({
        "referent-number": 32,
        "lower-bound": 32,
        "single-sufficiency": 32,
        "all-members-nonclaim": 32,
    })
    assert set(Counter(row["settlement_stratum"] for row in real).values()) == {16}
    assert all(row.get("comparator_kind") == "complete-careful-english-v1" for row in real)
    assert all(row["english"] != row["ainglish"] for row in items)
    assert all(row["answer"] in row["options"] and len(row["options"]) == len(set(row["options"])) for row in items)
    assert sha256(canonical(items)).hexdigest() == index["items_sha256"]
    original, digest = panel_harness.fetch_items(ORIGINAL_ITEMS_URL, ORIGINAL_ITEMS_SHA256)
    overlap = pairs(real) & pairs(original)
    assert not overlap
    report = {
        "kind": "dexagon.ainglish.they-number-longcat-replication-audit.v1",
        "scientific_items": len(real),
        "calibration_items": len(cal),
        "forms": index["forms"],
        "semantic_seams": index["semantic_seams"],
        "detailed_strata": index["detailed_strata"],
        "items_sha256": index["items_sha256"],
        "target_items_sha256": digest,
        "complete_pair_overlap_with_target": len(overlap),
        "reader_calls": 0,
        "passed": True,
    }
    report["content_sha256"] = sha256(canonical(report)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
