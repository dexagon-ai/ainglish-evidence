#!/usr/bin/env python3
"""Audit the panel-harness transformations without a model or network call."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    results = {}
    for name in ("average", "deletion"):
        source = json.loads((ROOT / f"{name}-comprehension-items.json").read_text(encoding="utf-8"))
        packet = json.loads((ROOT / f"{name}-panel.items.json").read_text(encoding="utf-8"))
        rows = packet["items"]
        assert hashlib.sha256(canonical(rows)).hexdigest() == packet["sha256"]
        assert packet["source_items_sha256"] == source["items_sha256"]
        calibration = [row for row in rows if row.get("calibration")]
        scientific = [row for row in rows if not row.get("calibration")]
        assert len(rows) == 492 and len(calibration) == 12 and len(scientific) == 480
        assert len({row["id"] for row in rows}) == 492
        assert [sum(row["options"].index(row["answer"]) == pos for row in calibration) for pos in range(3)] == [4, 4, 4]
        assert all(set(row) >= {"id", "english", "ainglish", "question", "options", "answer", "settlement_stratum"} for row in scientific)
        assert all(row["english"] and row["ainglish"] and row["english"] != row["ainglish"] for row in scientific)
        assert all(row["answer"] in row["options"] and len(row["options"]) == 3 for row in scientific)
        assert all(not ({"bare", "careful", "practical", "hidden_values"} & set(row)) for row in scientific)
        source_index = {row["id"]: row for row in source["items"]}
        for row in scientific:
            source_id, comparator = row["id"].rsplit("-", 1)
            original = source_index[source_id]
            assert comparator == row["comparison"]
            assert row["english"] == original[comparator]
            assert all(row[key] == original[key] for key in ("ainglish", "question", "options", "answer", "form", "hard_cell"))
        counts = Counter(row["settlement_stratum"] for row in scientific)
        assert len(counts) == (60 if name == "average" else 78)
        assert set(counts.values()) == ({8} if name == "average" else {6, 7})
        results[name] = {
            "items_sha256": packet["sha256"], "scientific": 480, "calibration": 12,
            "settlement_strata": len(counts), "per_stratum_counts": sorted(set(counts.values())),
        }
    print(json.dumps({
        "status": "panel_items_frozen", "targets": results,
        "model_calls": 0, "api_calls": 0, "governance_writes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
